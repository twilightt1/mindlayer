"use client";

import { useEffect, useState, useRef } from "react";
import { cn } from "@/lib/utils";

interface SparklesProps {
  className?: string;
  particleColor?: string;
  particleCount?: number;
  particleSize?: number;
  speed?: number;
  particleDensity?: number;
}

interface ParticleData {
  x: number;
  y: number;
  vx: number;
  vy: number;
  size: number;
  opacity: number;
  color: string;
}

export function Sparkles({
  className,
  particleColor = "#ffffff",
  particleCount = 50,
  particleSize = 2,
  speed = 1,
}: SparklesProps) {
  const [canvas, setCanvas] = useState<HTMLCanvasElement | null>(null);
  const animationRef = useRef<number>();
  const particlesRef = useRef<ParticleData[]>([]);

  useEffect(() => {
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const resize = () => {
      canvas.width = canvas.offsetWidth * window.devicePixelRatio;
      canvas.height = canvas.offsetHeight * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    };

    resize();
    window.addEventListener("resize", resize);

    const createParticle = (width: number, height: number): ParticleData => ({
      x: Math.random() * width,
      y: Math.random() * height,
      vx: (Math.random() - 0.5) * 0.5 * speed,
      vy: (Math.random() - 0.5) * 0.5 * speed,
      size: Math.random() * particleSize + 0.5,
      opacity: Math.random(),
      color: particleColor,
    });

    const updateParticle = (p: ParticleData, width: number, height: number) => {
      p.x += p.vx;
      p.y += p.vy;
      p.opacity -= 0.01 * speed;

      if (p.opacity <= 0) {
        p.x = Math.random() * width;
        p.y = Math.random() * height;
        p.opacity = 1;
      }

      if (p.x < 0) p.x = width;
      if (p.x > width) p.x = 0;
      if (p.y < 0) p.y = height;
      if (p.y > height) p.y = 0;
    };

    const drawParticle = (ctx: CanvasRenderingContext2D, p: ParticleData) => {
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = p.opacity;
      ctx.fill();
      ctx.globalAlpha = 1;
    };

    const width = canvas.offsetWidth;
    const height = canvas.offsetHeight;
    particlesRef.current = Array.from({ length: particleCount }, () => createParticle(width, height));

    const animate = () => {
      ctx.clearRect(0, 0, canvas.offsetWidth, canvas.offsetHeight);
      
      particlesRef.current.forEach((p) => {
        updateParticle(p, canvas.offsetWidth, canvas.offsetHeight);
        drawParticle(ctx, p);
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener("resize", resize);
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [canvas, particleColor, particleCount, particleSize, speed]);

  return (
    <canvas
      ref={setCanvas}
      className={cn("absolute inset-0 w-full h-full pointer-events-none", className)}
    />
  );
}
