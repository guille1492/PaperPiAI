import argparse
import json
import os
import random

import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image


def choose_prompt(filename: str) -> str:
    with open(filename) as f:
        prompts = json.load(f)
    return ' '.join(random.choice(part) for part in prompts)


def load_pipeline():
    pipe = AutoPipelineForText2Image.from_pretrained(
        "stabilityai/sdxl-turbo",
        torch_dtype=torch.float16,
        variant="fp16",
    )
    if torch.backends.mps.is_available():
        pipe = pipe.to("mps")
        print("Using MPS (Apple Metal) acceleration")
    else:
        pipe = pipe.to("cpu")
        print("MPS not available, using CPU")
    return pipe


parser = argparse.ArgumentParser(description="Generate preview images on Mac using SDXL-Turbo + MPS.")
parser.add_argument("output_dir", help="Directory to save the output images")
parser.add_argument("--prompts", default="prompts/flowers.json", help="Prompts file to use")
parser.add_argument("--prompt", default="", help="Override prompt")
parser.add_argument("--seed", type=int, default=None, help="Random seed")
parser.add_argument("--steps", type=int, default=4, help="Number of inference steps (4 is good for SDXL-Turbo)")
parser.add_argument("--width", type=int, default=640, help="Image width")
parser.add_argument("--height", type=int, default=400, help="Image height")
parser.add_argument("--count", type=int, default=1, help="Number of images to generate")
args = parser.parse_args()

os.makedirs(args.output_dir, exist_ok=True)

pipe = load_pipeline()

for i in range(args.count):
    prompt = args.prompt if args.prompt else choose_prompt(args.prompts)
    seed = args.seed if args.seed is not None else random.randint(1, 100000)

    print(f"\n[{i+1}/{args.count}] Prompt : {prompt}")
    print(f"         Seed   : {seed}")

    generator = torch.Generator().manual_seed(seed)
    image = pipe(
        prompt=prompt,
        num_inference_steps=args.steps,
        guidance_scale=0.0,   # SDXL-Turbo works best with guidance_scale=0
        width=args.width,
        height=args.height,
        generator=generator,
    ).images[0]

    filename = f"{prompt.replace(' ', '_')[:64]}_seed_{seed}.png"
    filepath = os.path.join(args.output_dir, filename)
    image.save(filepath)
    print(f"         Saved  : {filepath}")

print("\nDone.")
