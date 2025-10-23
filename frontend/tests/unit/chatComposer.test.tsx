import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect } from "vitest";

import { ChatPanel } from "../../src/features/chat/components/ChatPanel";

describe("ChatPanel composer", () => {
  it("renders composer controls and toggles submission state", async () => {
    render(<ChatPanel />);

    const messageInput = screen.getByRole("textbox", { name: /메시지 입력/i });
    const sendButton = screen.getByRole("button", { name: /전송/i });

    expect(sendButton).toBeDisabled();

    await userEvent.type(messageInput, "안녕하세요");

    expect(sendButton).toBeEnabled();
  });
});
