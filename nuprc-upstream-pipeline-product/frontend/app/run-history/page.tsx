import { redirect } from "next/navigation";

export default function RunHistoryRedirect() {
  redirect("/console/runs");
}
