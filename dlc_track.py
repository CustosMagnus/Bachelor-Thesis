import os
import sys
import glob
import shutil
from pathlib import Path

"""
DeepLabCut-based human motion tracking for t1.mp4 (or any provided video).

Requirements:
  - Python >= 3.9
  - DeepLabCut >= 2.3 (for create_pretrained_project with human model)
    Install: pip install "deeplabcut>=2.3"

This script will:
  1) Create a DeepLabCut pretrained human project (if it doesn't exist).
  2) Analyze the provided video with the pretrained human model.
  3) Create an overlaid (labeled) video.
  4) Copy the labeled video to ./temp/<name>_dlc_labeled.mp4 for easy access.

Notes:
  - The pretrained human model is designed for typical human pose landmarks.
  - No manual labeling or training is required for this flow.
"""


def ensure_dirs():
    # Match the app's folder creation behavior
    root = Path.cwd()
    (root / 'log').mkdir(exist_ok=True)
    (root / 'temp').mkdir(exist_ok=True)
    return root


def run_dlc_on_video(input_video: Path) -> Path:
    try:
        import deeplabcut as dlc
    except ImportError as e:
        raise RuntimeError(
            "DeepLabCut is not installed. Install it with: pip install \"deeplabcut>=2.3\""
        ) from e

    root = ensure_dirs()

    if not input_video.is_file():
        raise FileNotFoundError(f"Input video not found: {input_video}")

    # Create or reuse a pretrained project in the repository directory
    project_name = "HumanTracking"
    experimenter = "Auto"

    # DLC will create a time-stamped project folder; we'll capture config path
    # Use copy_videos=True so DLC manages its internal paths properly
    try:
        config_path = dlc.create_pretrained_project(
            project=project_name,
            experimenter=experimenter,
            videos=[str(input_video)],
            working_directory=str(root),
            copy_videos=True,
            model="human",
        )
    except TypeError:
        # Some DLC versions have positional-only signature but same order
        config_path = dlc.create_pretrained_project(
            project_name,
            experimenter,
            [str(input_video)],
            str(root),
            True,
            "human",
        )

    # Analyze and create labeled videos using DLC
    # The project directory is the parent of the returned config.yaml
    config_file = Path(config_path)
    project_dir = config_file.parent

    # The video inside the project is placed under the 'videos' folder with same basename
    project_video = project_dir / 'videos' / input_video.name
    if not project_video.exists():
        # Fallback: DLC may store in a different videos subdir; try to find it
        candidates = list((project_dir / 'videos').rglob(input_video.name))
        if candidates:
            project_video = candidates[0]
        else:
            raise FileNotFoundError(
                f"Could not find video {input_video.name} inside the DLC project at {project_dir / 'videos'}"
            )

    # Run analysis
    dlc.analyze_videos(str(config_file), [str(project_video)], save_as_csv=True)

    # Create labeled video overlay
    dlc.create_labeled_video(str(config_file), [str(project_video)], draw_skeleton=True)

    # DLC typically outputs labeled videos under 'labeled-videos'
    labeled_dir = project_dir / 'labeled-videos'
    if not labeled_dir.exists():
        # Some versions: 'labeled-data' contains frames only, but labeled videos are still under 'labeled-videos'
        # If the directory does not exist, search globally in project dir.
        labeled_candidates = list(project_dir.rglob("*_labeled.mp4"))
    else:
        labeled_candidates = list(labeled_dir.glob(f"{input_video.stem}*_labeled.mp4"))
        if not labeled_candidates:
            # Try a broader search in labeled-videos
            labeled_candidates = list(labeled_dir.glob("*_labeled.mp4"))

    if not labeled_candidates:
        # Final broad fallback
        labeled_candidates = list(project_dir.rglob("*_labeled.mp4"))

    if not labeled_candidates:
        raise RuntimeError("DeepLabCut labeled video was not produced or could not be located.")

    # Pick the most recent labeled video
    labeled_candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    labeled_video_path = labeled_candidates[0]

    # Copy to ./temp for convenience
    out_path = Path.cwd() / 'temp' / f"{input_video.stem}_dlc_labeled.mp4"
    shutil.copy2(labeled_video_path, out_path)
    return out_path


def main(argv: list[str]) -> None:
    root = ensure_dirs()

    if not argv:
        input_path = root / 't1.mp4'
    else:
        input_path = Path(argv[0])
        if not input_path.is_absolute():
            input_path = root / input_path

    out = run_dlc_on_video(input_path)
    print(f"Saved DeepLabCut labeled video to: {out}")


if __name__ == '__main__':
    main(sys.argv[1:])
