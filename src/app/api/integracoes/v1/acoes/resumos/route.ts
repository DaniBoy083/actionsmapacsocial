import { NextRequest } from "next/server";
import { integrationProxy } from "@/lib/integration-proxy";

export async function GET(request: NextRequest) {
  return integrationProxy(request, "acoes/resumos");
}
