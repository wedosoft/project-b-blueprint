import { useCallback, useMemo, useState } from "react";
import {
  Box,
  Button,
  FormControl,
  FormLabel,
  HStack,
  Textarea,
  VStack,
  Text,
  Badge,
  useToast,
  Spinner,
  Heading,
  Divider,
} from "@chakra-ui/react";
import { apiClient, type ConversationResponse, type Message } from "../../../lib/api/client";

export const ChatPanel = () => {
  const [message, setMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [conversation, setConversation] = useState<ConversationResponse | null>(null);
  const toast = useToast();

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
        const response = await apiClient.startConversation({
          message: {
            body: message.trim(),
          },
        });

        setConversation(response);
        setMessage("");

        toast({
          title: "메시지 전송 완료",
          description: response.pendingApproval
            ? "AI 응답이 검토 중입니다."
            : "AI 응답을 받았습니다.",
          status: response.pendingApproval ? "info" : "success",
          duration: 3000,
          isClosable: true,
        });
      } catch (error) {
        toast({
          title: "전송 실패",
          description: error instanceof Error ? error.message : "메시지 전송에 실패했습니다.",
          status: "error",
          duration: 5000,
          isClosable: true,
        });
      } finally {
        setIsSubmitting(false);
      }
    },
    [isSendDisabled, message, toast],
  );

  const renderMessage = (msg: Message) => {
    const isCustomer = msg.senderType === "customer";
    const isAI = msg.senderType === "ai";

    return (
      <Box
        key={msg.id}
        alignSelf={isCustomer ? "flex-end" : "flex-start"}
        maxW="70%"
        bg={isCustomer ? "blue.500" : isAI ? "green.100" : "gray.100"}
        color={isCustomer ? "white" : "black"}
        px={4}
        py={2}
        borderRadius="lg"
      >
        <HStack justify="space-between" mb={1}>
          <Text fontSize="xs" fontWeight="bold">
            {isCustomer ? "고객" : isAI ? "AI 상담원" : "상담원"}
          </Text>
          {msg.aiResponse && (
            <Badge
              colorScheme={
                msg.aiResponse.status === "approved"
                  ? "green"
                  : msg.aiResponse.status === "pending"
                  ? "yellow"
                  : "red"
              }
              fontSize="xs"
            >
              신뢰도: {(msg.aiResponse.confidence * 100).toFixed(0)}%
            </Badge>
          )}
        </HStack>
        <Text>{msg.body}</Text>
        <Text fontSize="xs" opacity={0.7} mt={1}>
          {new Date(msg.createdAt).toLocaleTimeString("ko-KR")}
        </Text>
      </Box>
    );
  };

  return (
    <Box as="section" p={4} borderWidth="1px" borderRadius="md" bg="white" h="100%">
      <VStack spacing={4} align="stretch" h="100%">
        <Heading size="md">고객 상담 채팅</Heading>

        {/* Messages area */}
        <Box
          flex={1}
          overflowY="auto"
          borderWidth="1px"
          borderRadius="md"
          p={4}
          bg="gray.50"
          minH="400px"
        >
          {conversation ? (
            <VStack spacing={3} align="stretch">
              {conversation.messages.map(renderMessage)}
              {conversation.pendingApproval && (
                <Box textAlign="center" py={2}>
                  <HStack justify="center" spacing={2}>
                    <Spinner size="sm" />
                    <Text fontSize="sm" color="gray.600">
                      상담원이 AI 응답을 검토 중입니다...
                    </Text>
                  </HStack>
                </Box>
              )}
            </VStack>
          ) : (
            <Box textAlign="center" py={8}>
              <Text color="gray.500">
                메시지를 입력하여 상담을 시작하세요
              </Text>
            </Box>
          )}
        </Box>

        <Divider />

        {/* Input form */}
        <form onSubmit={handleSubmit} noValidate>
          <FormControl>
            <FormLabel htmlFor="chat-message">메시지 입력</FormLabel>
            <Textarea
              id="chat-message"
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="상담 내용을 입력해 주세요."
              resize="vertical"
              minH="100px"
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
      </VStack>
    </Box>
  );
};
