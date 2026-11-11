#!/usr/bin/env python3
"""
CLI & Python client for controlling the live open Blender GUI via TCP JSON-RPC
(127.0.0.1:9876), with optional headless fallback via Blender --background.
"""

import argparse
import json
import os
import socket
import subprocess
import sys
from typing import Any, Dict, Optional

BLENDER_BIN = os.environ.get("BLENDER_BIN", "/Applications/Blender.app/Contents/MacOS/Blender")
DEFAULT_HOST = os.environ.get("BLENDER_CONTROL_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("BLENDER_CONTROL_PORT", "9876"))


def send_rpc(
    command: str,
    params: Optional[Dict[str, Any]] = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = 600.0,
) -> Dict[str, Any]:
    payload = {"command": command, "params": params or {}, "timeout": timeout}
    with socket.create_connection((host, port), timeout=min(timeout, 10.0)) as sock:
        sock.settimeout(timeout)
        sock.sendall((json.dumps(payload) + "\n").encode("utf-8"))
        buf = b""
        while not buf.endswith(b"\n"):
            chunk = sock.recv(65536)
            if not chunk:
                break
            buf += chunk
    if not buf:
        raise RuntimeError("Empty response from Blender bridge")
    resp = json.loads(buf.decode("utf-8"))
    if not resp.get("ok"):
        err = resp.get("error", "Unknown error")
        tb = resp.get("traceback", "")
        raise RuntimeError(f"Blender RPC error: {err}\n{tb}".strip())
    return resp["result"]


def run_headless(script_path: str, blend_file: Optional[str] = None, extra_args: Optional[list] = None) -> int:
    cmd = [BLENDER_BIN, "--background"]
    if blend_file:
        cmd.append(blend_file)
    cmd.extend(["--python", os.path.abspath(script_path)])
    if extra_args:
        cmd.append("--")
        cmd.extend(extra_args)
    proc = subprocess.run(cmd)
    return proc.returncode


def main():
    parser = argparse.ArgumentParser(description="Control live open Blender GUI or run headless jobs.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--timeout", type=float, default=600.0)

    sub = parser.add_subparsers(dest="subcommand", required=True)

    sub.add_parser("ping", help="Check live Blender GUI bridge connection")
    sub.add_parser("info", help="Inspect current live Blender scene objects, cameras, materials, and settings")
    sub.add_parser("reset", help="Clear all objects and unused datablocks in the live scene")

    p_exec = sub.add_parser("exec", help="Execute inline Python code on live Blender main thread")
    p_exec.add_argument("code", help="Python code string using bpy")

    p_run = sub.add_parser("run", help="Execute a Python script file in live Blender (or --headless)")
    p_run.add_argument("script", help="Path to .py script")
    p_run.add_argument("--headless", action="store_true", help="Run in isolated background Blender process")
    p_run.add_argument("--blend", help="Optional .blend file for --headless mode")

    p_view = sub.add_parser("viewport", help="Configure live Blender 3D viewport shading & camera view")
    p_view.add_argument("--shading", choices=["WIREFRAME", "SOLID", "MATERIAL", "RENDERED"], default="MATERIAL")
    p_view.add_argument("--no-camera", action="store_true", help="Do not switch viewport to active camera")

    p_shot = sub.add_parser("screenshot", help="Capture fast OpenGL/Metal viewport screenshot from live Blender")
    p_shot.add_argument("output", help="Output PNG path")

    p_render = sub.add_parser("render", help="Render high-quality still image from live Blender")
    p_render.add_argument("output", help="Output PNG path")
    p_render.add_argument("--engine", choices=["CYCLES", "BLENDER_EEVEE", "BLENDER_WORKBENCH"])
    p_render.add_argument("--samples", type=int)
    p_render.add_argument("--width", type=int)
    p_render.add_argument("--height", type=int)
    p_render.add_argument("--frame", type=int)

    p_anim = sub.add_parser("render-anim", help="Render animation (MP4 video or PNG sequence) from live Blender")
    p_anim.add_argument("output", help="Output .mp4 path (or frame prefix)")
    p_anim.add_argument("--engine", choices=["CYCLES", "BLENDER_EEVEE", "BLENDER_WORKBENCH"])
    p_anim.add_argument("--samples", type=int)
    p_anim.add_argument("--width", type=int)
    p_anim.add_argument("--height", type=int)
    p_anim.add_argument("--start", type=int)
    p_anim.add_argument("--end", type=int)
    p_anim.add_argument("--fps", type=int)

    p_save = sub.add_parser("save", help="Save live Blender scene to a .blend file")
    p_save.add_argument("filepath", help="Target .blend path")

    p_open = sub.add_parser("open", help="Open a .blend file in the live Blender GUI")
    p_open.add_argument("filepath", help="Source .blend path")

    args = parser.parse_args()

    if args.subcommand == "run" and args.headless:
        rc = run_headless(args.script, blend_file=args.blend)
        sys.exit(rc)

    if args.subcommand == "ping":
        res = send_rpc("ping", host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "info":
        res = send_rpc("get_scene_info", host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "reset":
        res = send_rpc("reset_scene", host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "exec":
        res = send_rpc("execute_code", {"code": args.code}, host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "run":
        res = send_rpc(
            "execute_file",
            {"path": os.path.abspath(args.script)},
            host=args.host,
            port=args.port,
            timeout=args.timeout,
        )
    elif args.subcommand == "viewport":
        res = send_rpc(
            "set_viewport",
            {"shading": args.shading, "camera_view": not args.no_camera},
            host=args.host,
            port=args.port,
            timeout=args.timeout,
        )
    elif args.subcommand == "screenshot":
        res = send_rpc(
            "viewport_screenshot",
            {"output_path": os.path.abspath(args.output)},
            host=args.host,
            port=args.port,
            timeout=args.timeout,
        )
    elif args.subcommand == "render":
        params: Dict[str, Any] = {"output_path": os.path.abspath(args.output)}
        if args.engine:
            params["engine"] = args.engine
        if args.samples:
            params["samples"] = args.samples
        if args.width:
            params["resolution_x"] = args.width
        if args.height:
            params["resolution_y"] = args.height
        if args.frame is not None:
            params["frame"] = args.frame
        res = send_rpc("render_image", params, host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "render-anim":
        params = {"output_path": os.path.abspath(args.output)}
        if args.engine:
            params["engine"] = args.engine
        if args.samples:
            params["samples"] = args.samples
        if args.width:
            params["resolution_x"] = args.width
        if args.height:
            params["resolution_y"] = args.height
        if args.start is not None:
            params["frame_start"] = args.start
        if args.end is not None:
            params["frame_end"] = args.end
        if args.fps is not None:
            params["fps"] = args.fps
        res = send_rpc("render_animation", params, host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "save":
        res = send_rpc("save_blend", {"filepath": os.path.abspath(args.filepath)}, host=args.host, port=args.port, timeout=args.timeout)
    elif args.subcommand == "open":
        res = send_rpc("open_blend", {"filepath": os.path.abspath(args.filepath)}, host=args.host, port=args.port, timeout=args.timeout)
    else:
        parser.error(f"Unhandled subcommand {args.subcommand}")
        return

    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
