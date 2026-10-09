/** Text with the dotted underline Duolingo puts under every word (hover hints in the original). */
export function Words({ text, highlight }: { text: string; highlight?: string }) {
  const marked = highlight ? text.split(new RegExp(`(${highlight.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "i")) : [text];
  return (
    <>
      {marked.map((part, partIndex) => {
        const isHighlight = highlight && part.toLowerCase() === highlight.toLowerCase();
        return part.split(/(\s+)/).map((word, wordIndex) =>
          /^\s+$/.test(word) || word === "" ? word : <span key={`${partIndex}-${wordIndex}`} className={`lx-word${isHighlight ? " lx-word-key" : ""}`}>{word}</span>,
        );
      })}
    </>
  );
}
