import { redirect } from "next/navigation";

export default function ControlPanelRedirect() {
  redirect("/console/pipeline");
}
