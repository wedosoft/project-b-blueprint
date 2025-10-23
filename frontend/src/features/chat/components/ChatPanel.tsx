import { useCallback, useMemo, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  HStack,
  Textarea,
} from "@chakra-ui/react";

export const ChatPanel = () => {
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const isSendDisabled = useMemo(
    () => isSubmitting || message.trim().length === 0,
    [isSubmitting, message],
  );

  const handleSubmit = useCallback(
    async (event: React.FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      if (isSendDisabled) {
        return;
      }

      setIsSubmitting(true);
      try {
        // TODO: 대화 생성 API 연동 (US1 구현 진행 시 적용)
      } finally {
        setIsSubmitting(false);
        setMessage("");
      }
    },
    [isSendDisabled],
  );

  return (
    <Box as="section" p={4} borderWidth="1px" borderRadius="md" bg="white">
      <form onSubmit={handleSubmit} noValidate>
        <FormControl>
          <FormLabel htmlFor="chat-message">메시지 입력</FormLabel>
          <Textarea
            id="chat-message"
            value={message}
            onChange={(event) => setMessage(event.target.value)}
            placeholder="상담 내용을 입력해 주세요."
            resize="vertical"
            minH="120px"
          />
        </FormControl>
        <HStack justify="flex-end" mt={3} spacing={3}>
          <Button
            type="submit"
            colorScheme="blue"
            isDisabled={isSendDisabled}
            isLoading={isSubmitting}
          >
            전송
          </Button>
        </HStack>
      </form>
    </Box>
  );
};
