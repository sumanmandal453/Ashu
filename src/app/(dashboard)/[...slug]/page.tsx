import Link from "next/link";
import { Construction } from "lucide-react";

export default function PlannedPage({ params }: { params: { slug: string[] } }) {
  const name = params.slug.join(" / ").replace(/-/g, " ");
  return (
    <div className="card mx-auto mt-10 max-w-lg text-center">
      <Construction className="mx-auto text-signal" />
      <h2 className="mt-3 font-display text-xl font-semibold capitalize">{name}</h2>
      <p className="mt-2 text-sm text-slate-500">This screen is next in the build order. No backend service is connected for it yet.</p>
      <Link href="/dashboard" className="mt-5 inline-block rounded-full bg-signal px-5 py-2 text-sm font-medium text-white">Back to overview</Link>
    </div>
  );
}
