import { DISCLAIMER_EN, DISCLAIMER_ZH } from "../../content/compliance";

export function DisclaimerBanner() {
  return (
    <aside className="disclaimer" role="note">
      <p>{DISCLAIMER_EN}</p>
      <p lang="zh-Hans">{DISCLAIMER_ZH}</p>
    </aside>
  );
}
