import { Box, Heading, SimpleGrid, Stat, StatLabel, StatNumber, StatHelpText, Card, CardBody, Text } from "@chakra-ui/react";

export const DashboardPage = () => {
  // Mock data for MVP - in production, fetch from API
  const metrics = {
    activeConversations: 12,
    avgConfidence: 0.82,
    approvalRate: 0.75,
    responseTimeP95: 2.8,
    escalations: 3,
  };

  return (
    <Box p={6}>
      <Heading size="lg" mb={6}>
        슈퍼바이저 대시보드
      </Heading>

      <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} spacing={6}>
        <Card>
          <CardBody>
            <Stat>
              <StatLabel>활성 대화</StatLabel>
              <StatNumber>{metrics.activeConversations}</StatNumber>
              <StatHelpText>현재 진행 중</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>평균 AI 신뢰도</StatLabel>
              <StatNumber>{(metrics.avgConfidence * 100).toFixed(0)}%</StatNumber>
              <StatHelpText>지난 24시간</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>승인율</StatLabel>
              <StatNumber>{(metrics.approvalRate * 100).toFixed(0)}%</StatNumber>
              <StatHelpText>수정 없이 승인</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>응답 시간 (P95)</StatLabel>
              <StatNumber>{metrics.responseTimeP95}초</StatNumber>
              <StatHelpText>95 백분위수</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>에스컬레이션</StatLabel>
              <StatNumber>{metrics.escalations}</StatNumber>
              <StatHelpText>오늘</StatHelpText>
            </Stat>
          </CardBody>
        </Card>

        <Card>
          <CardBody>
            <Stat>
              <StatLabel>시스템 상태</StatLabel>
              <StatNumber color="green.500">정상</StatNumber>
              <StatHelpText>모든 서비스 운영 중</StatHelpText>
            </Stat>
          </CardBody>
        </Card>
      </SimpleGrid>

      <Box mt={8} p={4} bg="blue.50" borderRadius="md">
        <Text fontWeight="bold" mb={2}>
          MVP 알림
        </Text>
        <Text fontSize="sm">
          이 대시보드는 MVP 버전입니다. 실시간 데이터는 향후 업데이트에서 제공됩니다.
        </Text>
      </Box>
    </Box>
  );
};
