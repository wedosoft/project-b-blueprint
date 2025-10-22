import { Stack, Box, Text, Button, HStack } from "@chakra-ui/react";

const App = () => {
  return (
    <Stack spacing={6}>
      <Box borderWidth="1px" borderRadius="lg" p={6}>
        <Text fontWeight="bold" mb={2}>
          개발 현황
        </Text>
        <Text>
          ⚙️ Phase 1 Setup 진행 중입니다. 백엔드와 프론트엔드 스켈레톤을 바탕으로 사용자 스토리를
          순차적으로 구현할 예정입니다.
        </Text>
      </Box>

      <Box borderWidth="1px" borderRadius="lg" p={6}>
        <Text fontWeight="bold" mb={2}>
          다음 단계 미리보기
        </Text>
        <HStack spacing={4} align="start">
          <Box flex={1}>
            <Text fontSize="sm" color="gray.500">
              고객 채팅 흐름 (US1)
            </Text>
            <Text>대화 생성, 메시지 스트리밍, 실시간 상태 표기를 구축합니다.</Text>
          </Box>
          <Box flex={1}>
            <Text fontSize="sm" color="gray.500">
              상담사 승인 (US2)
            </Text>
            <Text>승인 큐, 응답 수정/거부, 타임아웃 자동화를 구현합니다.</Text>
          </Box>
          <Box flex={1}>
            <Text fontSize="sm" color="gray.500">
              감독자 대시보드 (US3)
            </Text>
            <Text>핵심 KPI 및 실시간 모니터링 페이지를 제공합니다.</Text>
          </Box>
        </HStack>
      </Box>

      <Button colorScheme="blue" size="lg" alignSelf="flex-start">
        Vite 개발 서버 시작하기
      </Button>
    </Stack>
  );
};

export default App;
