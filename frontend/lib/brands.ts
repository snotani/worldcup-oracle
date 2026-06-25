// Visual identity for each model in the battle and each persona voice.
// Keyed by the short `name` the backend emits (claude, gpt, gemini, grok, composer).

export interface ModelBrand {
  label: string;
  provider: string;
  color: string;
  glyph: string; // short monogram shown in the avatar
}

const MODEL_BRANDS: Record<string, ModelBrand> = {
  claude: { label: "Claude", provider: "Anthropic", color: "#d97757", glyph: "✳" },
  gpt: { label: "GPT", provider: "OpenAI", color: "#10a37f", glyph: "◯" },
  gemini: { label: "Gemini", provider: "Google", color: "#4285f4", glyph: "✦" },
  grok: { label: "Grok", provider: "xAI", color: "#9aa4b2", glyph: "✕" },
  composer: { label: "Composer", provider: "Cursor", color: "#7c93ff", glyph: "▢" },
};

export function modelBrand(name: string): ModelBrand {
  const key = name.toLowerCase().split(/[:\-\s]/)[0];
  return (
    MODEL_BRANDS[key] ?? {
      label: name,
      provider: "Model",
      color: "#8d9bb5",
      glyph: name.slice(0, 1).toUpperCase(),
    }
  );
}

export interface PersonaBrand {
  emoji: string;
  color: string;
  gradient: string;
}

const PERSONA_BRANDS: Record<string, PersonaBrand> = {
  gaffer: {
    emoji: "🎩",
    color: "#3fbf7f",
    gradient: "linear-gradient(150deg, #15311f 0%, #0e1a14 70%)",
  },
  professor: {
    emoji: "🧠",
    color: "#6f9bff",
    gradient: "linear-gradient(150deg, #16213f 0%, #0d1424 70%)",
  },
  hypeman: {
    emoji: "🔥",
    color: "#ff9f43",
    gradient: "linear-gradient(150deg, #36210f 0%, #1c130a 70%)",
  },
};

export function personaBrand(id: string): PersonaBrand {
  return (
    PERSONA_BRANDS[id?.toLowerCase()] ?? {
      emoji: "🤖",
      color: "#9aa4b2",
      gradient: "linear-gradient(150deg, #1a2236 0%, #131a2b 70%)",
    }
  );
}
