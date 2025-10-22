import React from "react";
import ReactDOM from "react-dom/client";
import { ChakraProvider, Container, Heading, Text } from "@chakra-ui/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles.css";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <ChakraProvider>
      <QueryClientProvider client={queryClient}>
        <Container maxW="container.xl" py={12}>
          <Heading mb={4}>AI Contact Center MVP</Heading>
          <Text color="gray.500" mb={6}>
            채팅, 승인, 대시보드 기능을 단계적으로 구현하기 위한 프론트엔드 스켈레톤입니다.
          </Text>
          <App />
        </Container>
      </QueryClientProvider>
    </ChakraProvider>
  </React.StrictMode>,
);
