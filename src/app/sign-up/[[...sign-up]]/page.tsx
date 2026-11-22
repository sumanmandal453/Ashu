import { SignUp } from "@clerk/nextjs";
import { AuthCard, clerkAppearance } from "@/components/auth-card";

export default function SignUpPage() {
  return (
    <AuthCard title="Create your Ashu account">
      <SignUp routing="path" path="/sign-up" signInUrl="/sign-in" fallbackRedirectUrl="/dashboard" appearance={clerkAppearance} />
    </AuthCard>
  );
}
