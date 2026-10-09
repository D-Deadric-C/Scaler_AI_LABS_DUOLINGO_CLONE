import { Character } from "./Character";
import { ChatScene } from "./ChatScene";
import { SpeakerIcon } from "./Icons";
import { Words } from "./Words";
import { speak } from "./speech";
import { FillBlank } from "./exercises/FillBlank";
import { MatchPairs } from "./exercises/MatchPairs";
import { MultipleChoice } from "./exercises/MultipleChoice";
import { TypeAnswer } from "./exercises/TypeAnswer";
import { WordBank } from "./exercises/WordBank";
import type { ExerciseProps } from "./types";

function SpeakButton({ text, label }: { text: string; label: string }) {
  return <button type="button" className="lx-speak" aria-label={label} onClick={() => speak(text)}><SpeakerIcon /></button>;
}

function Bubble({ children, speakText }: { children: React.ReactNode; speakText?: string }) {
  return (
    <div className="lx-scene">
      <Character name="pip" size={110} />
      <div className="lx-bubble">
        {speakText ? <button type="button" className="lx-bubble-speak" aria-label="Play audio" onClick={() => speak(speakText)}><SpeakerIcon size={24} /></button> : null}
        <p><Words text={String(children)} /></p>
      </div>
    </div>
  );
}

const TITLES: Record<string, string> = {
  multiple_choice: "Read and respond",
  word_bank: "Translate this sentence",
  match_pairs: "Tap the matching pairs",
  fill_blank: "Fill in the blanks",
  type_answer: "Write this in Spanish",
};

/** The heading, optional scene and the interactive part for one exercise. */
export function ExerciseView(props: ExerciseProps) {
  const { exercise } = props;
  const payload = exercise.payload;
  const chat = exercise.type === "multiple_choice" ? (payload.chat as { line: string; character?: string; userCharacter?: string } | undefined) : undefined;
  const passage = exercise.type === "multiple_choice" ? ((payload.passage as string | undefined) ?? (payload.phrase as string | undefined)) : undefined;
  const highlight = (payload.highlight as string | undefined) ?? (payload.passage ? undefined : (payload.phrase as string | undefined));
  const question = (payload.question as string | undefined) ?? (payload.phrase ? `What does “${payload.phrase}” mean?` : exercise.prompt);
  const title = (payload.title as string | undefined) ?? (chat ? "Complete the chat" : TITLES[exercise.type]) ?? exercise.prompt;
  return (
    <section className="lx-exercise" aria-live="polite">
      <h1 className="lx-title">{title}</h1>
      {exercise.hint ? <p className="lx-hint">{exercise.hint}</p> : null}

      {chat ? <ChatScene line={chat.line} character={chat.character} userCharacter={chat.userCharacter} /> : null}
      {passage ? (
        <>
          <div className="lx-passage">
            <p><SpeakButton text={passage} label="Read the text aloud" /> <Words text={passage} highlight={highlight} /></p>
          </div>
          <p className="lx-question">{question}</p>
        </>
      ) : exercise.type === "multiple_choice" && !chat ? (
        <p className="lx-question">{question}</p>
      ) : null}

      {exercise.type === "word_bank" ? <Bubble speakText={String(payload.translation ?? "")}>{String(payload.translation ?? exercise.prompt)}</Bubble> : null}
      {exercise.type === "type_answer" ? <Bubble>{exercise.prompt.includes(":") ? exercise.prompt.split(":").slice(1).join(":").trim() : exercise.prompt}</Bubble> : null}

      {exercise.type === "multiple_choice" ? <MultipleChoice {...props} /> : null}
      {exercise.type === "word_bank" ? <WordBank {...props} /> : null}
      {exercise.type === "match_pairs" ? <MatchPairs {...props} /> : null}
      {exercise.type === "fill_blank" ? <FillBlank {...props} /> : null}
      {exercise.type === "type_answer" ? <TypeAnswer {...props} /> : null}
    </section>
  );
}
