"""
Blender Control Live Bridge (Startup Script for Blender 5.x)
Runs a localhost TCP JSON-RPC server (default 127.0.0.1:9876) on a daemon thread
and executes all bpy operations safely on Blender's main UI thread via bpy.app.timers.
"""

import contextlib
import io
import json
import math
import os
import queue
import socketserver
import sys
import threading
import time
import traceback

import bpy
import mathutils

HOST = os.environ.get("BLENDER_CONTROL_HOST", "127.0.0.1")
PORT = int(os.environ.get("BLENDER_CONTROL_PORT", "9876"))

_TASK_QUEUE: "queue.Queue[dict]" = queue.Queue()
_SERVER = None
_SERVER_THREAD = None


def _redraw_viewports():
    """Tag all open areas in GUI windows for immediate redraw."""
    wm = getattr(bpy.context, "window_manager", None)
    if not wm:
        return
    for window in wm.windows:
        screen = window.screen
        if not screen:
            continue
        for area in screen.areas:
            area.tag_redraw()


def _enable_metal_gpu():
    """Enable Apple Silicon Metal GPU acceleration for Cycles if available."""
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = "METAL"
        if hasattr(prefs, "refresh_devices"):
            prefs.refresh_devices()
        elif hasattr(prefs, "get_devices"):
            prefs.get_devices()
        enabled = []
        for dev in prefs.devices:
            if dev.type == "METAL":
                dev.use = True
                enabled.append(dev.name)
            else:
                dev.use = False
        bpy.context.scene.cycles.device = "GPU"
        return enabled
    except Exception as exc:
        return [f"GPU config warning: {exc}"]


def _handle_command_main_thread(req: dict) -> dict:
    cmd = req.get("command", "ping")
    params = req.get("params") or {}

    if cmd == "ping":
        scene = bpy.context.scene
        return {
            "status": "ok",
            "blender_version": bpy.app.version_string,
            "pid": os.getpid(),
            "background": bpy.app.background,
            "filepath": bpy.data.filepath,
            "scene": scene.name,
            "engine": scene.render.engine,
            "object_count": len(bpy.data.objects),
        }

    if cmd == "get_scene_info":
        scene = bpy.context.scene
        objects = []
        for obj in bpy.data.objects:
            objects.append({
                "name": obj.name,
                "type": obj.type,
                "location": [round(v, 4) for v in obj.location],
                "rotation_euler": [round(v, 4) for v in obj.rotation_euler],
                "scale": [round(v, 4) for v in obj.scale],
                "dimensions": [round(v, 4) for v in obj.dimensions],
                "visible": not obj.hide_render,
                "materials": [m.name for m in obj.data.materials if m] if hasattr(obj.data, "materials") and obj.data else [],
                "modifiers": [mod.type for mod in obj.modifiers],
            })
        return {
            "filepath": bpy.data.filepath,
            "scene_name": scene.name,
            "engine": scene.render.engine,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
            "fps": scene.render.fps,
            "frame_current": scene.frame_current,
            "frame_range": [scene.frame_start, scene.frame_end],
            "active_camera": scene.camera.name if scene.camera else None,
            "objects": objects,
            "materials": [m.name for m in bpy.data.materials],
        }

    if cmd in ("execute_code", "execute_file"):
        if cmd == "execute_file":
            script_path = os.path.abspath(params["path"])
            if not os.path.isfile(script_path):
                raise FileNotFoundError(f"Script not found: {script_path}")
            with open(script_path, "r", encoding="utf-8") as fh:
                code = fh.read()
        else:
            script_path = "<execute_code>"
            code = params["code"]

        stdout_buf = io.StringIO()
        stderr_buf = io.StringIO()
        exec_globals = {
            "__name__": "__main__",
            "__file__": script_path,
            "bpy": bpy,
            "math": math,
            "mathutils": mathutils,
            "SCRIPT_ARGS": params.get("args", {}),
            "enable_metal_gpu": _enable_metal_gpu,
        }
        t0 = time.time()
        with contextlib.redirect_stdout(stdout_buf), contextlib.redirect_stderr(stderr_buf):
            compiled = compile(code, script_path, "exec")
            exec(compiled, exec_globals)
        try:
            bpy.context.view_layer.update()
        except Exception:
            pass
        _redraw_viewports()
        return {
            "elapsed_sec": round(time.time() - t0, 3),
            "stdout": stdout_buf.getvalue(),
            "stderr": stderr_buf.getvalue(),
            "result": exec_globals.get("RESULT"),
        }

    if cmd == "set_viewport":
        shading_type = params.get("shading", "MATERIAL")  # SOLID, MATERIAL, RENDERED, WIREFRAME
        use_camera = params.get("camera_view", True)
        updated = 0
        wm = bpy.context.window_manager
        for window in wm.windows:
            for area in window.screen.areas:
                if area.type == "VIEW_3D":
                    for space in area.spaces:
                        if space.type == "VIEW_3D":
                            space.shading.type = shading_type
                            if shading_type == "MATERIAL":
                                space.shading.use_scene_lights = params.get("use_scene_lights", True)
                                space.shading.use_scene_world = params.get("use_scene_world", True)
                            if use_camera and bpy.context.scene.camera:
                                space.region_3d.view_perspective = "CAMERA"
                            elif "view_perspective" in params:
                                space.region_3d.view_perspective = params["view_perspective"]
                            updated += 1
                    area.tag_redraw()
        return {"updated_viewports": updated, "shading": shading_type, "camera_view": use_camera}

    if cmd == "viewport_screenshot":
        output_path = os.path.abspath(params["output_path"])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        scene = bpy.context.scene
        prev_path = scene.render.filepath
        prev_media = scene.render.image_settings.media_type
        prev_fmt = scene.render.image_settings.file_format
        try:
            scene.render.image_settings.media_type = "IMAGE"
            scene.render.image_settings.file_format = "PNG"
            scene.render.filepath = output_path
            wm = bpy.context.window_manager
            rendered = False
            for window in wm.windows:
                for area in window.screen.areas:
                    if area.type == "VIEW_3D":
                        region = next((r for r in area.regions if r.type == "WINDOW"), None)
                        with bpy.context.temp_override(window=window, area=area, region=region):
                            bpy.ops.render.opengl(write_still=True, view_context=True)
                            rendered = True
                            break
                if rendered:
                    break
            if not rendered:
                bpy.ops.render.opengl(write_still=True)
        finally:
            scene.render.filepath = prev_path
            scene.render.image_settings.media_type = prev_media
            scene.render.image_settings.file_format = prev_fmt
        return {"output_path": output_path, "exists": os.path.isfile(output_path)}

    if cmd == "render_image":
        output_path = os.path.abspath(params["output_path"])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        scene = bpy.context.scene
        if "engine" in params:
            scene.render.engine = params["engine"]
        gpu_devices = []
        if scene.render.engine == "CYCLES":
            gpu_devices = _enable_metal_gpu()
            if "samples" in params:
                scene.cycles.samples = int(params["samples"])
        elif scene.render.engine == "BLENDER_EEVEE" and "samples" in params:
            scene.eevee.taa_render_samples = int(params["samples"])

        if "resolution_x" in params:
            scene.render.resolution_x = int(params["resolution_x"])
        if "resolution_y" in params:
            scene.render.resolution_y = int(params["resolution_y"])
        if "frame" in params:
            scene.frame_set(int(params["frame"]))

        scene.render.image_settings.media_type = "IMAGE"
        scene.render.image_settings.file_format = params.get("file_format", "PNG")
        scene.render.filepath = output_path

        t0 = time.time()
        bpy.ops.render.render(write_still=True)
        elapsed = round(time.time() - t0, 3)
        _redraw_viewports()
        return {
            "output_path": output_path,
            "exists": os.path.isfile(output_path),
            "size_bytes": os.path.getsize(output_path) if os.path.isfile(output_path) else 0,
            "engine": scene.render.engine,
            "gpu_devices": gpu_devices,
            "elapsed_sec": elapsed,
        }

    if cmd == "render_animation":
        output_path = os.path.abspath(params["output_path"])
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        scene = bpy.context.scene
        if "engine" in params:
            scene.render.engine = params["engine"]
        gpu_devices = []
        if scene.render.engine == "CYCLES":
            gpu_devices = _enable_metal_gpu()
            if "samples" in params:
                scene.cycles.samples = int(params["samples"])
        elif scene.render.engine == "BLENDER_EEVEE" and "samples" in params:
            scene.eevee.taa_render_samples = int(params["samples"])

        if "resolution_x" in params:
            scene.render.resolution_x = int(params["resolution_x"])
        if "resolution_y" in params:
            scene.render.resolution_y = int(params["resolution_y"])
        if "frame_start" in params:
            scene.frame_start = int(params["frame_start"])
        if "frame_end" in params:
            scene.frame_end = int(params["frame_end"])
        if "fps" in params:
            scene.render.fps = int(params["fps"])

        video = params.get("video", output_path.lower().endswith((".mp4", ".mkv", ".mov")))
        if video:
            scene.render.image_settings.media_type = "VIDEO"
            scene.render.ffmpeg.format = params.get("container", "MPEG4")
            scene.render.ffmpeg.codec = params.get("codec", "H264")
            scene.render.ffmpeg.constant_rate_factor = params.get("quality", "HIGH")
            scene.render.ffmpeg.ffmpeg_preset = "GOOD"
            scene.render.use_file_extension = False
        else:
            scene.render.image_settings.media_type = "IMAGE"
            scene.render.image_settings.file_format = "PNG"
            scene.render.use_file_extension = True

        # Blender treats '#' in scene.render.filepath as frame-number padding!
        # Render to a '#' free temp path if needed, then move atomically to output_path.
        safe_path = output_path.replace("#", "_HASH_") if "#" in os.path.basename(output_path) else output_path
        scene.render.filepath = safe_path
        t0 = time.time()
        bpy.ops.render.render(animation=True)
        if safe_path != output_path and os.path.isfile(safe_path):
            os.replace(safe_path, output_path)
        elapsed = round(time.time() - t0, 3)
        _redraw_viewports()
        return {
            "output_path": output_path,
            "exists": os.path.isfile(output_path),
            "size_bytes": os.path.getsize(output_path) if os.path.isfile(output_path) else 0,
            "frames": [scene.frame_start, scene.frame_end],
            "engine": scene.render.engine,
            "gpu_devices": gpu_devices,
            "elapsed_sec": elapsed,
        }

    if cmd == "save_blend":
        filepath = os.path.abspath(params["filepath"])
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=filepath)
        return {"filepath": filepath, "exists": os.path.isfile(filepath)}

    if cmd == "open_blend":
        filepath = os.path.abspath(params["filepath"])
        if not os.path.isfile(filepath):
            raise FileNotFoundError(f"Blend file not found: {filepath}")
        bpy.ops.wm.open_mainfile(filepath=filepath)
        _redraw_viewports()
        return {"filepath": bpy.data.filepath, "scene": bpy.context.scene.name}

    if cmd == "reset_scene":
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for block_collection in (
            bpy.data.meshes,
            bpy.data.materials,
            bpy.data.lights,
            bpy.data.cameras,
            bpy.data.curves,
            bpy.data.node_groups,
            bpy.data.actions,
        ):
            for block in list(block_collection):
                if block.users == 0:
                    block_collection.remove(block)
        _redraw_viewports()
        return {"status": "cleared"}

    raise ValueError(f"Unknown command: {cmd}")


def _process_queue() -> float:
    """Main-thread timer callback executed every 50ms in Blender."""
    while True:
        try:
            item = _TASK_QUEUE.get_nowait()
        except queue.Empty:
            break
        try:
            data = _handle_command_main_thread(item["request"])
            item["response"] = {"ok": True, "result": data}
        except Exception as exc:
            item["response"] = {
                "ok": False,
                "error": str(exc),
                "traceback": traceback.format_exc(),
            }
        finally:
            item["event"].set()
    return 0.05


class _ReusableTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class _BridgeRequestHandler(socketserver.StreamRequestHandler):
    def handle(self):
        while True:
            line = self.rfile.readline()
            if not line:
                break
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line.decode("utf-8"))
            except Exception as exc:
                resp = {"ok": False, "error": f"Invalid JSON: {exc}"}
                self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
                self.wfile.flush()
                continue

            done_event = threading.Event()
            item = {"request": req, "event": done_event, "response": None}
            _TASK_QUEUE.put(item)
            timeout = float(req.get("timeout", 600.0))
            if not done_event.wait(timeout=timeout):
                resp = {"ok": False, "error": f"Timed out waiting {timeout}s for Blender main thread"}
            else:
                resp = item["response"]
            self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
            self.wfile.flush()


@bpy.app.handlers.persistent
def _ensure_timer_on_load(_dummy):
    if not bpy.app.timers.is_registered(_process_queue):
        bpy.app.timers.register(_process_queue, first_interval=0.05, persistent=True)


def start_bridge():
    global _SERVER, _SERVER_THREAD
    if bpy.app.background and os.environ.get("BLENDER_BRIDGE_FORCE") != "1":
        return
    if _SERVER is not None:
        return
    try:
        _SERVER = _ReusableTCPServer((HOST, PORT), _BridgeRequestHandler)
    except OSError as exc:
        print(f"[BlenderControlBridge] Port {HOST}:{PORT} already in use ({exc}); skipping.")
        return

    _SERVER_THREAD = threading.Thread(
        target=_SERVER.serve_forever,
        name="BlenderControlBridgeServer",
        daemon=True,
    )
    _SERVER_THREAD.start()

    if not bpy.app.timers.is_registered(_process_queue):
        bpy.app.timers.register(_process_queue, first_interval=0.05, persistent=True)
    if _ensure_timer_on_load not in bpy.app.handlers.load_post:
        bpy.app.handlers.load_post.append(_ensure_timer_on_load)

    print(f"[BlenderControlBridge] Listening on {HOST}:{PORT} (PID {os.getpid()})")


def register():
    start_bridge()


def unregister():
    global _SERVER
    if _SERVER is not None:
        _SERVER.shutdown()
        _SERVER.server_close()
        _SERVER = None
    if bpy.app.timers.is_registered(_process_queue):
        bpy.app.timers.unregister(_process_queue)


if __name__ == "__main__":
    register()
