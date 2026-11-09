import React, { useRef, useCallback } from 'react';

interface DualRangeSliderProps {
  minBound: number;
  maxBound: number;
  currentMin: number;
  currentMax: number;
  onChange: (min: number, max: number) => void;
}

export const DualRangeSlider: React.FC<DualRangeSliderProps> = ({
  minBound,
  maxBound,
  currentMin,
  currentMax,
  onChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const range = maxBound - minBound || 1;
  const leftPercent = Math.max(0, Math.min(100, ((currentMin - minBound) / range) * 100));
  const rightPercent = Math.max(0, Math.min(100, ((currentMax - minBound) / range) * 100));

  const handlePointerDown = (which: 'min' | 'max') => (e: React.PointerEvent) => {
    e.preventDefault();
    const target = e.currentTarget;
    target.setPointerCapture(e.pointerId);

    const onPointerMove = (moveEvent: PointerEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const clientX = Math.max(rect.left, Math.min(rect.right, moveEvent.clientX));
      const ratio = (clientX - rect.left) / rect.width;
      const rawVal = minBound + ratio * range;

      if (which === 'min') {
        const newMin = Math.min(rawVal, currentMax);
        onChange(newMin, currentMax);
      } else {
        const newMax = Math.max(rawVal, currentMin);
        onChange(currentMin, newMax);
      }
    };

    const onPointerUp = (upEvent: PointerEvent) => {
      target.releasePointerCapture(upEvent.pointerId);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('pointerup', onPointerUp);
    };

    window.addEventListener('pointermove', onPointerMove);
    window.addEventListener('pointerup', onPointerUp);
  };

  return (
    <div className="slider-container" ref={containerRef}>
      <div className="slider-track" />
      <div
        className="slider-fill"
        style={{
          left: `${leftPercent}%`,
          width: `${Math.max(0, rightPercent - leftPercent)}%`,
        }}
      />
      <div
        className="slider-thumb-handle"
        style={{ left: `${leftPercent}%` }}
        onPointerDown={handlePointerDown('min')}
        title={`Min: ${currentMin.toFixed(2)}`}
      />
      <div
        className="slider-thumb-handle"
        style={{ left: `${rightPercent}%` }}
        onPointerDown={handlePointerDown('max')}
        title={`Max: ${currentMax.toFixed(2)}`}
      />
    </div>
  );
};
