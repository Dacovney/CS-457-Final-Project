# AI Prompting and Constraints
AI can implement the design, but it can not change the design.

## Purpose
- AI assists with implementation of the already-designed protocol.
- AI should generate code that follows the specification.
- AI should not invent new message types, fields, states, or framing rules.
- Human reviews generated code before it becomes part of the project.

## Protocol Source of Truth
- protocol_blueprint.md is authoritative. If an AI's assumptions conflict with it, the Markdown specification wins. The AI should ask for clarification rather than silently changing the protocol.

## Prompt: Serialization / Framing
Prompts must include:
- JSON
- UTF-8 encoding
- 4-byte unsigned big-endian length prefix
- receiver must read exactly 4 bytes first
- then read exactly the specified payload length
- handle partial recv() calls
- don't assume one recv() equals one message
- don't use newline delimiters
- don't invent another framing method

## Prompt Message Parser
Prompts must include:
- Validate msg_type
- Validate required fields
- Validate field data types
- Reject malformed JSON
- Reject unknown/unsupported message types
- Return structured errors
- Don't modify game state when validation fails
- Follow the exact schemas in protocol_blueprint.md

## Prompt: Server State Handling
Prompts must include:
- Server is authoritative.
- State transitions must follow fsm_specification.md.
- Clients cannot directly change game state.
- Only the active player can perform HIT/STAND.
- Invalid actions produce ERROR and leave the FSM state unchanged.
- Disconnects must follow the documented forfeit behavior.
- Don't add states or transitions without explicit approval.

## Prompt: Client Implementation
Prompts must include:
- Send only valid messages defined by the protocol.
- Never assume a server response arrives in one TCP recv().
- Use the same framing/parser functions as specified.
- Display server errors rather than trying to correct/reinterpret them locally.
- Keep game-state authority on the server.
- Handle server disconnects gracefully.

## Constraint / Verification Strategy
To ensure code correctness regardless of AI confidence:
- Compare generated code against protocol_blueprint.md.
- Compare state-handling logic against fsm_specification.md.
- Test every message type.
- Test malformed JSON.
- Test missing fields.
- Test invalid field types.
- Test out-of-turn moves.
- Test TCP fragmentation/coalescing.
- Test intentional DISCONNECT.
- Test unexpected socket closure.
- Manually review AI-generated code before committing it.
- Do not accept an AI-generated change if it modifies the protocol without updating the specification first.