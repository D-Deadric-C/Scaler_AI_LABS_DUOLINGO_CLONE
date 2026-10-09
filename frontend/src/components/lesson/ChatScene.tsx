import { Character } from "./Character";
import { SpeakerIcon } from "./Icons";
import { Words } from "./Words";
import { speak } from "./speech";

type Props = { line: string; character?: string; userCharacter?: string };

/** "Complete the chat": a character speaks and the learner's avatar waits to answer. */
export function ChatScene({ line, character = "mia", userCharacter = "kai" }: Props) {
  return (
    <div className="lx-chat">
      <div className="lx-chat-row">
        <Character name={character} size={56} />
        <div className="lx-bubble lx-bubble-left">
          <button type="button" className="lx-bubble-speak" aria-label="Play audio" onClick={() => speak(line)}><SpeakerIcon size={30} /></button>
          <p><Words text={line} /></p>
        </div>
      </div>
      <div className="lx-chat-row lx-chat-right">
        <div className="lx-bubble lx-bubble-right"><span className="lx-blank-line" /></div>
        <Character name={userCharacter} size={56} />
      </div>
    </div>
  );
}
