import LegalPage from "@/components/LegalPage";

function H({ children }) {
  return <h2 className="pt-2 text-sm font-bold text-foreground">{children}</h2>;
}

export default function Terms() {
  return (
    <LegalPage title="Terms & Conditions" updated="7 August 2026">
      <p>These terms govern your use of Listrix. By creating an account, you agree to them. If you do not agree, do not create an account.</p>

      <H>1. What Listrix is</H>
      <p>
        Listrix is a business tool that helps you turn your inventory into priced marketplace listings. It is provided
        as software for your business operations, with AI assistance where enabled.
      </p>

      <H>2. Your account</H>
      <p>
        You are responsible for keeping your sign-in details safe and for the activity on your account. Each account is
        scoped to your own workspace and your data is kept separate from other users&apos; data.
      </p>

      <H>3. Your data</H>
      <p>
        Your inventory, listings, prices and settings belong to you. We do not sell your data. Data is stored on the
        hosting you choose (by default, a self-hosted database on your own computer or server). Passwords are stored
        scrambled and marketplace credentials are stored encrypted. See the Privacy Policy for details.
      </p>

      <H>4. AI assistance</H>
      <p>
        AI features generate suggestions only. Nothing is posted, published or changed externally without your explicit
        approval. AI output should be checked by you before use.
      </p>

      <H>5. Acceptable use</H>
      <p>
        You agree not to misuse the service: no attempting to access other users&apos; data, no abusing the AI, and no
        using Listrix for unlawful activity.
      </p>

      <H>6. Service availability</H>
      <p>
        Listrix is provided as-is. We work to keep it reliable but do not guarantee uninterrupted availability, and are
        not liable for losses from downtime, data entry mistakes, or AI suggestions.
      </p>

      <H>7. Changes to these terms</H>
      <p>
        We may update these terms as the service evolves. Significant changes will be shown to you, and continued use
        after a change means you accept the updated terms.
      </p>

      <H>8. Contact</H>
      <p>Questions about these terms can be raised through the app&apos;s support channels or your Terilliom representative.</p>
    </LegalPage>
  );
}
