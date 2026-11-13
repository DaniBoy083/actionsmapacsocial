import { OperationalAction } from "@/features/clinical/operational-action";

export default async function ActionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <OperationalAction id={id} />;
}
