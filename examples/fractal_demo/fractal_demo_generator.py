#!/usr/bin/env python3
"""
Fractal Demo Generator for GoldenSeed

This script demonstrates procedural generation with fractals using GoldenSeed's
deterministic entropy streams. Generates Mandelbrot and Julia set fractals with
seed-based color schemes, showcasing how tiny seeds can create complex, reproducible
visual patterns.

This enhanced version features Phi (Golden Ratio) focused zoom animations that
highlight mathematically significant regions within fractals, demonstrating the
deep connection between the Golden Ratio and fractal geometry.

⚠️ NOT FOR CRYPTOGRAPHY: This is for procedural generation demonstrations only.

Usage:
    python fractal_demo_generator.py                             # Generate all outputs
    python fractal_demo_generator.py --static-only               # Generate only static images
    python fractal_demo_generator.py --animated-only             # Generate only animations
    python fractal_demo_generator.py --seed 42                   # Use specific seed for colors
    python fractal_demo_generator.py --zoom-target phi           # Focus on Phi regions
    python fractal_demo_generator.py --zoom-target phi_squared   # Focus on Φ² regions
    python fractal_demo_generator.py --fractal-type julia        # Generate Julia animations
    python fractal_demo_generator.py --fractal-type both         # Generate both types

Requirements:
    pip install pillow numpy imageio

Features:
    - Deterministic color palettes from seeds
    - HD static images (1920x1080)
    - Smooth zoom animations with Phi-focused targets
    - Multiple zoom targets: phi, phi_squared, phi_conjugate, golden_spiral
    - Mandelbrot and Julia set animations
    - Golden Ratio mathematical demonstrations (Φ, Φ², 1/Φ)
"""

import argparse
import os
import sys
from pathlib import Path
import math

try:
    import numpy as np
    from PIL import Image
except ImportError:
    print("Error: Required packages not installed.")
    print("Please run: pip install pillow numpy")
    sys.exit(1)

# Optional: imageio for animations
try:
    import imageio
    HAS_IMAGEIO = True
except ImportError:
    HAS_IMAGEIO = False

# Import GoldenSeed
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
from gq import UniversalQKD

# Golden Ratio constant - fundamental to both GoldenSeed and fractal geometry
PHI = (1 + math.sqrt(5)) / 2  # ≈ 1.618033988749895
PHI_SQUARED = PHI * PHI  # ≈ 2.618
PHI_CUBED = PHI * PHI * PHI  # ≈ 4.236

# Zoom target configurations showcasing mathematically significant regions
ZOOM_TARGETS = {
    'phi': {
        'mandelbrot': {
            'center': (-0.4, 1/PHI - 1),  # Phi-spiral region in upper boundary
            'description': 'Phi-spiral region - exhibits Golden Ratio proportions',
            'zoom_factor': 1.18  # ~Φ/√2 for aesthetically pleasing zoom rate
        },
        'julia': {
            'c_real': -1/PHI,  # Golden Ratio reciprocal
            'c_imag': 0.0,
            'center': (0.0, 0.0),
            'description': 'Julia set with c=-1/Φ - demonstrates Phi symmetry',
            'zoom_factor': 1.15
        }
    },
    'phi_squared': {
        'mandelbrot': {
            'center': (-1/PHI_SQUARED, 1/PHI_SQUARED),  # Φ² region
            'description': 'Region scaled by Φ² (≈2.618) - deeper golden proportions',
            'zoom_factor': 1.19  # Slightly faster zoom for Φ² regions
        },
        'julia': {
            'c_real': -1/PHI_SQUARED,
            'c_imag': 1/PHI_SQUARED,
            'center': (0.0, 0.0),
            'description': 'Julia set with c=-1/Φ²+i/Φ² - second-order Phi influence',
            'zoom_factor': 1.16
        }
    },
    'phi_conjugate': {
        'mandelbrot': {
            'center': (-1/PHI, 1/PHI),  # Reciprocal golden ratio
            'description': 'Golden ratio conjugate region - inverse Phi scaling',
            'zoom_factor': 1.17
        },
        'julia': {
            'c_real': 1/PHI - 1,  # (1-Φ)/Φ
            'c_imag': 1/PHI,
            'center': (0.0, 0.0),
            'description': 'Julia set with conjugate Phi parameters',
            'zoom_factor': 1.14
        }
    },
    'default': {
        'mandelbrot': {
            'center': (-0.7, 0.0),
            'description': 'Classic zoom into main cardioid region',
            'zoom_factor': 1.15
        },
        'julia': {
            'c_real': -0.4,
            'c_imag': 0.6,
            'center': (0.0, 0.0),
            'description': 'Classic Julia set parameters',
            'zoom_factor': 1.12
        }
    },
    'golden_spiral': {
        'mandelbrot': {
            'center': (-PHI/2, 0.0),  # Golden angle region
            'description': 'Golden angle region near secondary bulb',
            'zoom_factor': 1.17
        },
        'julia': {
            'c_real': -PHI + 1,  # Φ - 1 = 1/Φ
            'c_imag': PHI - 1,
            'center': (0.0, 0.0),
            'description': 'Julia set with c=-1/Φ+i/Φ - double Phi influence',
            'zoom_factor': 1.14
        }
    }
}


class FractalGenerator:
    """Generate deterministic fractals using GoldenSeed entropy."""
    
    def __init__(self, seed_offset=0):
        """
        Initialize fractal generator with a seed.
        
        Args:
            seed_offset: Seed offset for deterministic color generation
        """
        self.seed_offset = seed_offset
        self.generator = UniversalQKD()
        
        # Skip to seed-specific position
        for _ in range(seed_offset):
            next(self.generator)
    
    def get_color_palette(self, num_colors=256):
        """
        Generate a deterministic color palette from seed.
        
        Args:
            num_colors: Number of colors in palette (default: 256)
            
        Returns:
            List of RGB tuples
        """
        colors = []
        for _ in range(num_colors):
            color_bytes = next(self.generator)
            r = color_bytes[0]
            g = color_bytes[1]
            b = color_bytes[2]
            colors.append((r, g, b))
        return colors
    
    def mandelbrot(self, width, height, x_min=-2.5, x_max=1.0, 
                   y_min=-1.0, y_max=1.0, max_iter=256):
        """
        Generate Mandelbrot set.
        
        Args:
            width, height: Image dimensions
            x_min, x_max, y_min, y_max: Complex plane bounds
            max_iter: Maximum iterations
            
        Returns:
            2D numpy array of iteration counts
        """
        x = np.linspace(x_min, x_max, width)
        y = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x, y)
        C = X + 1j * Y
        
        Z = np.zeros_like(C)
        M = np.zeros(C.shape, dtype=int)
        
        for i in range(max_iter):
            mask = np.abs(Z) <= 2
            Z[mask] = Z[mask]**2 + C[mask]
            M[mask] = i
        
        return M
    
    def julia(self, width, height, c_real=-0.4, c_imag=0.6,
              x_min=-1.5, x_max=1.5, y_min=-1.5, y_max=1.5, max_iter=256):
        """
        Generate Julia set.
        
        Args:
            width, height: Image dimensions
            c_real, c_imag: Julia set constant
            x_min, x_max, y_min, y_max: Complex plane bounds
            max_iter: Maximum iterations
            
        Returns:
            2D numpy array of iteration counts
        """
        x = np.linspace(x_min, x_max, width)
        y = np.linspace(y_min, y_max, height)
        X, Y = np.meshgrid(x, y)
        Z = X + 1j * Y
        
        c = complex(c_real, c_imag)
        M = np.zeros(Z.shape, dtype=int)
        
        for i in range(max_iter):
            mask = np.abs(Z) <= 2
            Z[mask] = Z[mask]**2 + c
            M[mask] = i
        
        return M
    
    def apply_color_palette(self, fractal_data, palette):
        """
        Apply color palette to fractal data.
        
        Args:
            fractal_data: 2D array of iteration counts
            palette: List of RGB tuples
            
        Returns:
            PIL Image
        """
        height, width = fractal_data.shape
        img = Image.new('RGB', (width, height))
        pixels = img.load()
        
        max_val = len(palette) - 1
        
        for y in range(height):
            for x in range(width):
                color_idx = fractal_data[y, x] % len(palette)
                pixels[x, y] = palette[color_idx]
        
        return img
    
    def generate_static_mandelbrot(self, output_path, width=1920, height=1080):
        """Generate static Mandelbrot fractal image."""
        print(f"Generating Mandelbrot set ({width}x{height})...")
        
        # Generate color palette
        palette = self.get_color_palette()
        
        # Generate fractal
        fractal_data = self.mandelbrot(width, height)
        
        # Apply colors
        img = self.apply_color_palette(fractal_data, palette)
        
        # Save
        img.save(output_path)
        print(f"  ✓ Saved: {output_path}")
    
    def generate_static_julia(self, output_path, width=1920, height=1080):
        """Generate static Julia set fractal image."""
        print(f"Generating Julia set ({width}x{height})...")
        
        # Generate color palette (using different seed position)
        for _ in range(100):
            next(self.generator)
        palette = self.get_color_palette()
        
        # Generate fractal
        fractal_data = self.julia(width, height)
        
        # Apply colors
        img = self.apply_color_palette(fractal_data, palette)
        
        # Save
        img.save(output_path)
        print(f"  ✓ Saved: {output_path}")
    
    def generate_zoom_animation(self, output_path, fractal_type='mandelbrot',
                                frames=30, width=1920, height=1080, zoom_target='phi'):
        """
        Generate zoom animation as GIF focusing on mathematically significant regions.
        
        Args:
            output_path: Output file path (.gif)
            fractal_type: 'mandelbrot' or 'julia'
            frames: Number of frames
            width, height: Frame dimensions
            zoom_target: Zoom target configuration ('phi', 'default', 'golden_spiral')
                        'phi' - focuses on Golden Ratio related regions
                        'golden_spiral' - emphasizes golden angle and spiral patterns
                        'default' - classic interesting regions
        """
        if not HAS_IMAGEIO:
            print("  ⚠ Skipping animation: imageio not installed")
            print("  Install with: pip install imageio")
            return
        
        # Get zoom configuration
        if zoom_target not in ZOOM_TARGETS:
            print(f"  ⚠ Unknown zoom target '{zoom_target}', using 'phi'")
            zoom_target = 'phi'
        
        config = ZOOM_TARGETS[zoom_target][fractal_type]
        
        print(f"Generating {fractal_type} zoom animation ({frames} frames)...")
        print(f"  Target: {zoom_target} - {config['description']}")
        
        # Generate color palette
        palette = self.get_color_palette()
        
        # Generate frames with zoom
        images = []
        
        if fractal_type == 'mandelbrot':
            # Zoom into Phi-related or other interesting region
            center_x, center_y = config['center']
            zoom_factor = config['zoom_factor']
            
            for i in range(frames):
                zoom = zoom_factor ** i
                # Use aspect-ratio-aware spans for proper rendering
                span_x = 3.5 / zoom
                span_y = 2.0 / zoom
                
                x_min = center_x - span_x / 2
                x_max = center_x + span_x / 2
                y_min = center_y - span_y / 2
                y_max = center_y + span_y / 2
                
                # Use lower resolution for animation to keep file size reasonable
                frame_width = width // 2
                frame_height = height // 2
                
                fractal_data = self.mandelbrot(
                    frame_width, frame_height, x_min, x_max, y_min, y_max
                )
                img = self.apply_color_palette(fractal_data, palette)
                images.append(np.array(img))
                
                if (i + 1) % 10 == 0:
                    print(f"  Frame {i + 1}/{frames} (zoom: {zoom:.2f}x)")
        
        else:  # julia
            # Use Phi-related Julia parameters if specified
            c_real = config.get('c_real', -0.4)
            c_imag = config.get('c_imag', 0.6)
            center_x, center_y = config['center']
            zoom_factor = config['zoom_factor']
            
            print(f"  Julia parameter c = {c_real:.4f} + {c_imag:.4f}i")
            
            for i in range(frames):
                zoom = zoom_factor ** i
                span = 3.0 / zoom
                
                x_min = center_x - span / 2
                x_max = center_x + span / 2
                y_min = center_y - span / 2
                y_max = center_y + span / 2
                
                # Use lower resolution for animation
                frame_width = width // 2
                frame_height = height // 2
                
                fractal_data = self.julia(
                    frame_width, frame_height, 
                    c_real=c_real, c_imag=c_imag,
                    x_min=x_min, x_max=x_max, 
                    y_min=y_min, y_max=y_max
                )
                img = self.apply_color_palette(fractal_data, palette)
                images.append(np.array(img))
                
                if (i + 1) % 10 == 0:
                    print(f"  Frame {i + 1}/{frames} (zoom: {zoom:.2f}x)")
        
        # Save as GIF
        imageio.mimsave(output_path, images, duration=0.1, loop=0)
        print(f"  ✓ Saved: {output_path}")
        print(f"  Mathematical significance: {config['description']}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate deterministic fractals using GoldenSeed",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fractal_demo_generator.py                             # Generate all outputs
  python fractal_demo_generator.py --static-only               # Only static images
  python fractal_demo_generator.py --animated-only             # Only animations
  python fractal_demo_generator.py --seed 42                   # Use seed 42
  python fractal_demo_generator.py --zoom-target phi           # Focus on Phi regions
  python fractal_demo_generator.py --zoom-target phi_squared   # Phi² regions
  python fractal_demo_generator.py --fractal-type julia        # Julia set animations

Zoom Targets:
  phi              - Golden Ratio focused regions (demonstrates Φ ≈ 1.618)
  phi_squared      - Φ² scaled regions (demonstrates Φ² ≈ 2.618)
  phi_conjugate    - Golden ratio conjugate regions (1/Φ scaling)
  golden_spiral    - Golden angle and spiral patterns  
  default          - Classic interesting fractal regions
        """
    )
    
    parser.add_argument('--static-only', action='store_true',
                       help='Generate only static images')
    parser.add_argument('--animated-only', action='store_true',
                       help='Generate only animations (requires imageio)')
    parser.add_argument('--seed', type=int, default=0,
                       help='Seed offset for color generation (default: 0)')
    parser.add_argument('--output-dir', type=str, default='outputs',
                       help='Output directory (default: outputs)')
    parser.add_argument('--zoom-target', type=str, default='phi',
                       choices=['phi', 'phi_squared', 'phi_conjugate', 'default', 'golden_spiral'],
                       help='Zoom target for animations (default: phi)')
    parser.add_argument('--fractal-type', type=str, default='mandelbrot',
                       choices=['mandelbrot', 'julia', 'both'],
                       help='Type of fractal animation to generate (default: mandelbrot)')
    
    args = parser.parse_args()
    
    # Determine output directory
    script_dir = Path(__file__).parent
    output_dir = script_dir / args.output_dir
    output_dir.mkdir(exist_ok=True)
    
    # Initialize generator
    generator = FractalGenerator(seed_offset=args.seed)
    
    print("=" * 70)
    print("GoldenSeed Fractal Demo Generator")
    print("=" * 70)
    print(f"Seed offset: {args.seed}")
    print(f"Output directory: {output_dir}")
    print(f"Zoom target: {args.zoom_target}")
    print(f"Golden Ratio (Φ): {PHI:.15f}")
    print()
    
    # Generate outputs
    generate_static = not args.animated_only
    generate_animated = not args.static_only
    
    if generate_static:
        print("Generating static images...")
        print("-" * 70)
        
        generator.generate_static_mandelbrot(
            output_dir / f"mandelbrot_seed{args.seed}.png"
        )
        
        generator.generate_static_julia(
            output_dir / f"julia_seed{args.seed}.png"
        )
        
        print()
    
    if generate_animated:
        print("Generating animations...")
        print("-" * 70)
        
        if not HAS_IMAGEIO:
            print("⚠ Warning: imageio not installed, skipping animations")
            print("Install with: pip install imageio")
        else:
            # Determine which fractal types to generate
            generate_mandelbrot = args.fractal_type in ['mandelbrot', 'both']
            generate_julia_anim = args.fractal_type in ['julia', 'both']
            
            if generate_mandelbrot:
                generator.generate_zoom_animation(
                    output_dir / f"mandelbrot_zoom_{args.zoom_target}_seed{args.seed}.gif",
                    fractal_type='mandelbrot',
                    frames=30,
                    zoom_target=args.zoom_target
                )
                print()
            
            if generate_julia_anim:
                generator.generate_zoom_animation(
                    output_dir / f"julia_zoom_{args.zoom_target}_seed{args.seed}.gif",
                    fractal_type='julia',
                    frames=30,
                    zoom_target=args.zoom_target
                )
                print()
    
    print("=" * 70)
    print("✓ Generation complete!")
    print("=" * 70)
    print()
    print(f"View your fractals in: {output_dir}/")
    print()
    
    # Display mathematical insights based on zoom target
    if args.zoom_target == 'phi':
        print("🌟 Phi (Golden Ratio) Insight:")
        print(f"The golden ratio Φ ≈ {PHI:.6f} appears throughout nature and")
        print("mathematics. In fractals, Phi-related regions often exhibit")
        print("special symmetries and self-similar patterns at golden proportions.")
        print(f"These animations zoom into regions where Φ's influence is visible!")
        print()
    elif args.zoom_target == 'phi_squared':
        print("🌟 Phi² Insight:")
        print(f"Phi squared (Φ²) ≈ {PHI_SQUARED:.6f} represents the second power of")
        print("the golden ratio. This value appears in advanced golden proportions")
        print("and creates deeper self-similarity in fractal structures.")
        print()
    elif args.zoom_target == 'phi_conjugate':
        print("🌟 Golden Ratio Conjugate Insight:")
        print(f"The golden ratio conjugate (1/Φ) ≈ {1/PHI:.6f} is intimately related")
        print("to Φ through the identity Φ - 1 = 1/Φ. This creates unique symmetries")
        print("in fractal patterns where inverse scaling reveals hidden structure.")
        print()
    elif args.zoom_target == 'golden_spiral':
        print("🌟 Golden Spiral Insight:")
        print("The golden angle (≈137.5°) and spiral patterns based on Φ appear")
        print("frequently in nature (sunflower seeds, nautilus shells, galaxies).")
        print("These zoom targets showcase spiral-like fractal features.")
        print()
    
    print("Key insight: These complex patterns are generated from")
    print(f"a single seed value ({args.seed}), demonstrating how")
    print("GoldenSeed creates deterministic, reproducible outputs")
    print("from tiny fixed seeds!")


if __name__ == "__main__":
    main()
