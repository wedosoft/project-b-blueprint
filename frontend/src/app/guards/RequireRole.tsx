import { ReactNode } from "react";

type RequireRoleProps = {
  role: "customer" | "agent" | "supervisor";
  children: ReactNode;
};

export const RequireRole = ({ children }: RequireRoleProps) => {
  // TODO: 권한 확인 로직을 Supabase Auth와 연동한다.
  return <>{children}</>;
};
