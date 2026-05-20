import { redirect } from "next/navigation";

/** Legacy route — product docs moved to /docs */
export default function ApisRedirectPage() {
  redirect("/docs");
}
