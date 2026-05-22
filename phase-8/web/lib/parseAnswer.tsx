import React from "react";
import { escapeHtml, parseAnswerSegments } from "./answerSegments";

export { escapeHtml, parseAnswerSegments } from "./answerSegments";

export function AnswerBody({ text }: { text: string }) {
  const lines = text.split("\n");
  return (
    <div className="space-y-2 text-[15px] leading-relaxed text-app-text">
      {lines.map((line, li) => {
        if (!line.trim()) return <br key={`br-${li}`} />;
        const segs = parseAnswerSegments(line);
        return (
          <p key={li} className="whitespace-pre-wrap break-words">
            {segs.map((s, i) =>
              s.type === "text" ? (
                <span key={i} dangerouslySetInnerHTML={{ __html: escapeHtml(s.value) }} />
              ) : (
                <a
                  key={i}
                  href={s.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-groww-dark underline underline-offset-2 hover:text-groww"
                >
                  {escapeHtml(s.label)}
                </a>
              )
            )}
          </p>
        );
      })}
    </div>
  );
}
