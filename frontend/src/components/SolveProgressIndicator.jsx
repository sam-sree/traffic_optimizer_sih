import React, { useEffect, useState } from 'react';
import { Check, Loader2, Sparkles, Cpu, Layers } from 'lucide-react';

const STAGES = [
  {
    id: 'clustering',
    name: 'Clustering',
    detail: 'Partitioning delivery nodes & applying capacity constraints',
    icon: Layers
  },
  {
    id: 'subtours',
    name: 'Exact sub-tours',
    detail: 'Solving exact branch-and-cut TSP sub-routes per cluster',
    icon: Cpu
  },
  {
    id: 'stitching',
    name: 'QPSO stitching',
    detail: 'Quantum-Inspired Swarm Optimization & global path stitching',
    icon: Sparkles
  }
];

export default function SolveProgressIndicator({ loading, algorithm }) {
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [elapsedMs, setElapsedMs] = useState(0);

  useEffect(() => {
    if (!loading) {
      setCurrentStageIndex(0);
      setElapsedMs(0);
      return;
    }

    const startTime = Date.now();
    const timerInterval = setInterval(() => {
      setElapsedMs(Date.now() - startTime);
    }, 100);

    const stage1Timeout = setTimeout(() => setCurrentStageIndex(1), 700);
    const stage2Timeout = setTimeout(() => setCurrentStageIndex(2), 1500);

    return () => {
      clearInterval(timerInterval);
      clearTimeout(stage1Timeout);
      clearTimeout(stage2Timeout);
    };
  }, [loading]);

  if (!loading) return null;

  const progressPercent = Math.min(100, Math.round(((currentStageIndex + 0.6) / STAGES.length) * 100));

  return (
    <div className="staged-solver-banner" role="status" aria-live="polite">
      <div className="staged-solver-head">
        <div className="staged-solver-title">
          <Loader2 className="spin text-indigo-400" size={18} />
          <div>
            <h4>Optimizing Route Execution</h4>
            <p className="algorithm-tag">{algorithm || 'Hybrid QPSO + Exact-Cluster'}</p>
          </div>
        </div>
        <div className="staged-solver-timer">
          <span className="timer-badge">{(elapsedMs / 1000).toFixed(1)}s</span>
        </div>
      </div>

      {/* Progress Track */}
      <div className="progress-bar-container">
        <div className="progress-bar-fill" style={{ width: `${progressPercent}%` }} />
      </div>

      {/* 3-Stage Pipeline */}
      <div className="staged-pipeline">
        {STAGES.map((stage, idx) => {
          const isDone = idx < currentStageIndex;
          const isActive = idx === currentStageIndex;
          const StageIcon = stage.icon;

          return (
            <div
              key={stage.id}
              className={`stage-item ${isDone ? 'done' : ''} ${isActive ? 'active' : ''}`}
            >
              <div className="stage-icon-box">
                {isDone ? (
                  <Check size={14} className="check-icon" />
                ) : isActive ? (
                  <Loader2 size={14} className="spin active-spinner" />
                ) : (
                  <StageIcon size={14} className="pending-icon" />
                )}
              </div>
              <div className="stage-text">
                <span className="stage-name">{stage.name}</span>
                {isActive && <small className="stage-detail">{stage.detail}</small>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
