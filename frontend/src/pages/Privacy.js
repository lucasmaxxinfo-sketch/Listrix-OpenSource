import LegalPage from "@/components/LegalPage";

function H({ children }) {
  return <h2 className="pt-2 text-sm font-bold text-foreground">{children}</h2>;
}

export default function Privacy() {
  return (
    <LegalPage title="Privacy Policy" updated="7 August 2026">
      <p>This policy explains what data Listrix collects, how it is stored and protected, and what choices you have.</p>

      <H>1. What we collect</H>
      <p>
        Account details (email and display name), your inventory and listing data, pricing and sales records you enter,
        activity logs, and optional marketplace credentials you choose to connect.
      </p>

      <H>2. How data is stored</H>
      <p>
        Listrix is local-first. By default your data lives in a database on your own computer or server and never leaves
        it unless you connect an external marketplace. There are no third-party analytics or tracking scripts.
      </p>

      <H>3. Security</H>
      <p>
        Passwords are scrambled (hashed) so they can never be read back. Marketplace credentials are encrypted before
        storage. Sessions use secure tokens, and each workspace is isolated so other users cannot see your data.
      </p>

      <H>4. AI processing</H>
      <p>
        By default, AI runs on your own machine using open-source models (no cloud, no API key). If you configure a
        remote AI provider, prompts and item details may be sent to that provider; you control this in Settings.
      </p>

      <H>5. What we do NOT do</H>
      <p>
        We do not sell your data, we do not show ads, and we do not share your information with third parties except
        where you explicitly connect a marketplace or service yourself.
      </p>

      <H>6. Your choices</H>
      <p>
        You can delete your data at any time by clearing your local database or deleting your account. Disconnecting a
        marketplace stops that data flow. You are not required to accept any marketing.
      </p>

      <H>7. Changes</H>
      <p>
        If this policy changes in a meaningful way, the updated version will be shown in the app and the &quot;Last
        updated&quot; date above will change.
      </p>

      <H>8. Contact</H>
      <p>Privacy questions can be raised through the app&apos;s support channels or your Terilliom representative.</p>
    </LegalPage>
  );
}
