import { SignIn } from "@clerk/nextjs";
import { AuthCard, clerkAppearance } from "@/components/auth-card";

export default function SignInPage() {
  return (
    <AuthCard title="Sign in to continue">
      <SignIn routing="path" path="/sign-in" signUpUrl="/sign-up" fallbackRedirectUrl="/dashboard" appearance={clerkAppearance} />
    </AuthCard>
  );
}
