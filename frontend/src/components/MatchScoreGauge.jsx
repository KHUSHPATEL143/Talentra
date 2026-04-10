import PropTypes from "prop-types";
import { useEffect, useMemo, useState } from "react";

function getGaugeColor(score) {
  if (score >= 80) return "#22c55e";
  if (score >= 60) return "#eab308";
  if (score >= 40) return "#f97316";
  return "#ef4444";
}

export default function MatchScoreGauge({ score, grade }) {
  const [animatedScore, setAnimatedScore] = useState(0);
  const radius = 72;
  const circumference = 2 * Math.PI * radius;
  const progress = useMemo(() => Math.min(Math.max(animatedScore, 0), 100) / 100, [animatedScore]);
  const dashOffset = circumference * (1 - progress);
  const color = getGaugeColor(score);

  useEffect(() => {
    let frameId;
    const startedAt = performance.now();
    const duration = 1000;

    const tick = (timestamp) => {
      const elapsed = timestamp - startedAt;
      const nextScore = Math.min(score, (elapsed / duration) * score);
      setAnimatedScore(nextScore);
      if (elapsed < duration) {
        frameId = requestAnimationFrame(tick);
      }
    };

    frameId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frameId);
  }, [score]);

  return (
    <div className="rounded-3xl bg-white p-6 shadow-panel">
      <svg viewBox="0 0 200 200" className="mx-auto h-60 w-60">
        <circle cx="100" cy="100" r={radius} stroke="#e2e8f0" strokeWidth="16" fill="none" />
        <circle
          cx="100"
          cy="100"
          r={radius}
          stroke={color}
          strokeWidth="16"
          fill="none"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          transform="rotate(-90 100 100)"
        />
        <text x="100" y="96" textAnchor="middle" className="fill-slate-900 text-4xl font-bold">
          {grade}
        </text>
        <text x="100" y="126" textAnchor="middle" className="fill-slate-500 text-base font-medium">
          {animatedScore.toFixed(1)} / 100
        </text>
      </svg>
      <p className="mt-2 text-center text-sm text-slate-500">Semantic fit score across required and preferred skills</p>
    </div>
  );
}

MatchScoreGauge.propTypes = {
  score: PropTypes.number.isRequired,
  grade: PropTypes.string.isRequired
};
