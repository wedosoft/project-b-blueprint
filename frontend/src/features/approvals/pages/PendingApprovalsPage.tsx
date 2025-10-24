import { useState, useEffect } from "react";
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  Badge,
  Textarea,
  useToast,
  Spinner,
  Card,
  CardHeader,
  CardBody,
  CardFooter,
  Divider,
} from "@chakra-ui/react";
import { apiClient, type PendingApproval } from "../../../lib/api/client";

export const PendingApprovalsPage = () => {
  const [approvals, setApprovals] = useState<PendingApproval[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedApproval, setSelectedApproval] = useState<string | null>(null);
  const [modifiedText, setModifiedText] = useState("");
  const [agentNotes, setAgentNotes] = useState("");
  const toast = useToast();

  // Mock organization ID for MVP - in production, get from auth context
  const MOCK_ORG_ID = "00000000-0000-0000-0000-000000000001";
  const MOCK_AGENT_ID = "00000000-0000-0000-0000-000000000002";

  useEffect(() => {
    loadPendingApprovals();
    // Refresh every 10 seconds
    const interval = setInterval(loadPendingApprovals, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadPendingApprovals = async () => {
    try {
      const data = await apiClient.listPendingApprovals(MOCK_ORG_ID);
      setApprovals(data);
    } catch (error) {
      toast({
        title: "조회 실패",
        description: error instanceof Error ? error.message : "승인 대기 목록을 불러올 수 없습니다.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (approval: PendingApproval) => {
    try {
      const result = await apiClient.approveResponse(approval.aiResponseId, {
        action: "approved",
        agentId: MOCK_AGENT_ID,
        notes: agentNotes || undefined,
      });

      toast({
        title: "승인 완료",
        description: result.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });

      // Remove from list
      setApprovals(prev => prev.filter(a => a.aiResponseId !== approval.aiResponseId));
      setAgentNotes("");
    } catch (error) {
      toast({
        title: "승인 실패",
        description: error instanceof Error ? error.message : "승인 처리에 실패했습니다.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleModify = async (approval: PendingApproval) => {
    if (!modifiedText.trim()) {
      toast({
        title: "수정 내용 필요",
        description: "수정된 응답 내용을 입력해 주세요.",
        status: "warning",
        duration: 3000,
        isClosable: true,
      });
      return;
    }

    try {
      const result = await apiClient.approveResponse(approval.aiResponseId, {
        action: "modified",
        agentId: MOCK_AGENT_ID,
        submittedText: modifiedText,
        notes: agentNotes || undefined,
      });

      toast({
        title: "수정 승인 완료",
        description: result.message,
        status: "success",
        duration: 3000,
        isClosable: true,
      });

      setApprovals(prev => prev.filter(a => a.aiResponseId !== approval.aiResponseId));
      setSelectedApproval(null);
      setModifiedText("");
      setAgentNotes("");
    } catch (error) {
      toast({
        title: "수정 실패",
        description: error instanceof Error ? error.message : "수정 처리에 실패했습니다.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  const handleReject = async (approval: PendingApproval) => {
    try {
      const result = await apiClient.approveResponse(approval.aiResponseId, {
        action: "rejected",
        agentId: MOCK_AGENT_ID,
        notes: agentNotes || "응답 품질 부족",
      });

      toast({
        title: "거부 완료",
        description: result.message,
        status: "info",
        duration: 3000,
        isClosable: true,
      });

      setApprovals(prev => prev.filter(a => a.aiResponseId !== approval.aiResponseId));
      setAgentNotes("");
    } catch (error) {
      toast({
        title: "거부 실패",
        description: error instanceof Error ? error.message : "거부 처리에 실패했습니다.",
        status: "error",
        duration: 5000,
        isClosable: true,
      });
    }
  };

  if (loading) {
    return (
      <Box textAlign="center" py={10}>
        <Spinner size="xl" />
        <Text mt={4}>승인 대기 목록을 불러오는 중...</Text>
      </Box>
    );
  }

  return (
    <Box p={6}>
      <VStack align="stretch" spacing={6}>
        <HStack justify="space-between">
          <Heading size="lg">AI 응답 승인 대기 ({approvals.length})</Heading>
          <Button onClick={loadPendingApprovals} size="sm">
            새로고침
          </Button>
        </HStack>

        {approvals.length === 0 ? (
          <Box textAlign="center" py={10} bg="gray.50" borderRadius="md">
            <Text fontSize="lg" color="gray.600">
              승인 대기 중인 응답이 없습니다
            </Text>
          </Box>
        ) : (
          approvals.map((approval) => (
            <Card key={approval.aiResponseId} variant="outline">
              <CardHeader>
                <HStack justify="space-between">
                  <VStack align="start" spacing={1}>
                    <HStack>
                      <Badge colorScheme="purple">{approval.priority}</Badge>
                      <Badge
                        colorScheme={
                          approval.confidence >= 0.75 ? "green" : "yellow"
                        }
                      >
                        신뢰도: {(approval.confidence * 100).toFixed(0)}%
                      </Badge>
                    </HStack>
                    <Text fontSize="sm" color="gray.600">
                      대기 시간: {new Date(approval.waitingSince).toLocaleString("ko-KR")}
                    </Text>
                  </VStack>
                </HStack>
              </CardHeader>

              <CardBody>
                <VStack align="stretch" spacing={4}>
                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      고객 질문:
                    </Text>
                    <Box bg="blue.50" p={3} borderRadius="md">
                      <Text>{approval.customerMessage}</Text>
                    </Box>
                  </Box>

                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      AI 제안 응답:
                    </Text>
                    <Box bg="green.50" p={3} borderRadius="md">
                      <Text>{approval.proposedResponse}</Text>
                    </Box>
                  </Box>

                  {selectedApproval === approval.aiResponseId && (
                    <>
                      <Divider />
                      <Box>
                        <Text fontWeight="bold" mb={2}>
                          수정된 응답:
                        </Text>
                        <Textarea
                          value={modifiedText}
                          onChange={(e) => setModifiedText(e.target.value)}
                          placeholder="수정된 응답을 입력하세요..."
                          minH="100px"
                        />
                      </Box>
                    </>
                  )}

                  <Box>
                    <Text fontWeight="bold" mb={2}>
                      상담원 메모 (선택사항):
                    </Text>
                    <Textarea
                      value={agentNotes}
                      onChange={(e) => setAgentNotes(e.target.value)}
                      placeholder="승인/거부 사유 또는 메모..."
                      size="sm"
                    />
                  </Box>
                </VStack>
              </CardBody>

              <CardFooter>
                <HStack spacing={3} width="100%" justify="flex-end">
                  {selectedApproval === approval.aiResponseId ? (
                    <>
                      <Button
                        colorScheme="blue"
                        onClick={() => handleModify(approval)}
                      >
                        수정 승인
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => {
                          setSelectedApproval(null);
                          setModifiedText("");
                        }}
                      >
                        수정 취소
                      </Button>
                    </>
                  ) : (
                    <>
                      <Button
                        colorScheme="green"
                        onClick={() => handleApprove(approval)}
                      >
                        승인
                      </Button>
                      <Button
                        colorScheme="yellow"
                        onClick={() => {
                          setSelectedApproval(approval.aiResponseId);
                          setModifiedText(approval.proposedResponse);
                        }}
                      >
                        수정
                      </Button>
                      <Button
                        colorScheme="red"
                        onClick={() => handleReject(approval)}
                      >
                        거부
                      </Button>
                    </>
                  )}
                </HStack>
              </CardFooter>
            </Card>
          ))
        )}
      </VStack>
    </Box>
  );
};
