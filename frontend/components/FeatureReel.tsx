import type { AgentFeature } from "@/lib/types";

export default function FeatureReel({ features }: { features: AgentFeature[] }) {
  return (
    <div className="feature-reel">
      {features.map((f, i) => (
        <div className="feature-chip" key={f.key} style={{ animationDelay: `${i * 70}ms` }}>
          <span className="feature-num">{i + 1}</span>
          <div>
            <div className="feature-label">{f.label}</div>
            <div className="feature-detail">{f.detail}</div>
          </div>
        </div>
      ))}
    </div>
  );
}
