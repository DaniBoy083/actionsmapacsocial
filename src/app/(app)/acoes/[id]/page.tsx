import { Suspense } from "react";
import { ActionDetail } from "@/features/actions/action-detail";
async function Detail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <ActionDetail id={id} />;
}
export default function ActionPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return (
    <Suspense fallback={<p role="status">Carregando ação…</p>}>
      <Detail params={params} />
    </Suspense>
  );
}
