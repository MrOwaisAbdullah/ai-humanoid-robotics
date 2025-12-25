---
name: better-auth-v2
description: Production-ready authentication system using Better Auth v2 with latest features. Includes OAuth providers, advanced RBAC, multi-tenant support, and security best practices.
category: authentication
version: 2.0.0
dependencies:
  - better-auth: "^1.3.0"
  - better-auth/adapters: prisma|drizzle|kysely|mongodb
  - better-auth/plugins: organization|oauth|two-factor|passkey
---

# Better Auth v2 Integration Skill

## Purpose

Provides **cutting-edge authentication templates** and **expert integration guidance** using Better Auth v2. This skill analyzes your project architecture and implements a full-featured authentication system including:
- Email/password and OAuth authentication (Google, Apple, Facebook, X, etc.)
- Advanced OAuth token encryption and account linking
- Multi-factor authentication (2FA) support
- Role-Based Access Control (RBAC) with fine-grained permissions
- Multi-tenant architecture with organizations
- Session management with enhanced security
- Production-ready security configurations
- **Personalized onboarding flows** for user background collection

## What This Skill Provides

✅ **Automated Implementation Plan**: Analyzes project structure (framework, DB, backend) and provides a tailored integration strategy.
✅ **Latest Better Auth v2 configuration templates**
✅ **Enhanced database schemas** (Prisma, Drizzle, Kysely, MongoDB)
✅ **Modern React/Vue/Svelte authentication clients**
✅ **Middleware for route protection with advanced features**
✅ **Fine-grained RBAC and permission utilities**
✅ **OAuth provider setup with token encryption**
✅ **2FA and passkey authentication templates**
✅ **Advanced security configurations**
✅ **Separate Backend Creation**: For static/SSR-incompatible sites, creates a dedicated Hono + Node.js backend.

## What This Skill Does NOT Provide

❌ Custom business logic implementation (use better-auth-specialist subagent)
❌ Database migration scripts execution (provides the scripts, does not run them)
❌ OAuth credential provisioning (you must provide Client IDs/Secrets)
❌ Production deployment without security review

## When to Use This Skill

Use this skill when:
- Building new applications with modern authentication requirements
- Migrating from older auth systems to Better Auth v2
- Implementing enterprise-grade security features
- Setting up multi-tenant SaaS applications
- Requiring advanced OAuth features like token encryption
- Needing 2FA or passkey authentication
- User wants personalized onboarding questions after signup
- Project uses Next.js, Remix, Astro, Vite, SvelteKit, Nuxt, or pure React

**How to use:**
```
Load the better-auth-v2 skill and use the [template-name] for [framework] with [database-adapter]
OR
Simply ask: "Add Better-Auth to my project" to start the automated integrator flow.
```

## How This Skill Works (Step-by-Step Execution)

1. **Project Analysis Phase**
   - Detect framework (Next.js App Router, Pages Router, Remix, Astro, SvelteKit, etc.)
   - Determine if SSR/SSG/static
   - Check for existing backend (Node/Express, tRPC, Hono, etc.)
   - Detect existing database setup and ORM (Prisma, Drizzle, TypeORM, raw SQL, etc.)

2. **Database Strategy**
   - If a database is already configured → ask for connection string/credentials (only after explicit user confirmation)
   - If no database → ask user preference (PostgreSQL recommended) and guide creation (e.g., Supabase, Neon, Railway, PlanetScale)
   - Only after user says “yes, go ahead”, create required Better-Auth tables/schema automatically

3. **Backend Setup**
   - If project supports SSR/API routes → add Better-Auth directly inside the project
   - If static or incompatible → create separate backend repo/folder using Hono + Node.js/Express (deployable to Vercel, Railway, Fly.io, etc.)
   - Always use Drizzle ORM (Better-Auth’s preferred adapter) with PostgreSQL

4. **Better-Auth Core Implementation**
   - Install `better-auth` + `better-auth-ui` + required plugins (google, apple, facebook, twitter)
   - Configure env variables for all OAuth providers
   - Set up email/password + magic links as fallback
   - Add user metadata table/extension for background questionnaire answers

5. **Onboarding Flow**
   - After first successful sign-up → redirect to `/onboarding`
   - Multi-step form asking:
     - Years of programming experience
     - Primary languages/frameworks
     - Hardware (Mac/Windows/Linux, CPU, GPU, RAM)
     - Development focus (frontend/backend/full-stack/AI/ML/mobile)
   - Store answers in `user_metadata` table for future personalization

6. **UI Integration (Better-Auth-UI)**
   - Create `/sign-in`, `/sign-up` pages with `<AuthUI />`
   - Add header component with dynamic auth buttons:
     - Guest → “Sign In” | “Sign Up”
     - Logged in → Avatar + Dropdown with “Profile”, “Settings”, “Sign Out”
   - Fully responsive, accessible, dark mode ready

7. **Session Management & Protection**
   - Server-side session validation
   - `authClient` React hook for frontend state
   - Protected routes middleware (Next.js middleware or route guards)

## Output You Will Receive

After activation, I will deliver:

- Complete step-by-step implementation plan tailored to your exact project
- Exact terminal commands to run
- File-by-file code changes/additions
- `.env.example` with all required variables
- Database schema (Drizzle migrations)
- Separate backend repo link (if needed)
- Ready-to-copy onboarding questionnaire component
- Header component with conditional auth UI
- Fully working, production-ready authentication system

## Example Usage

**User says:**  
“I have a Next.js 14 App Router site using Prisma + PostgreSQL on Supabase. Add Better-Auth with Google, Apple, Facebook, X login and ask users about their dev experience after signup.”

**This Skill Instantly Activates → Delivers:**

- Confirmed DB usage (no new DB needed)
- Prisma → Drizzle migration plan (or dual-ORM strategy if preferred)
- `/src/auth` folder structure with full Better-Auth config
- All OAuth callbacks configured
- `/app/(auth)/sign-in/[[...better-auth]]/page.tsx` using `<AuthUI />`
- Header with dynamic auth state
- `/app/onboarding/page.tsx` with questionnaire
- Protected route example using middleware

**User says:**  
“My site is a static Astro + React site. Just add login with social providers.”

**This Skill Responds:**  
→ Creates separate `better-auth-backend/` folder (Hono + Node)  
→ Deploys in < 2 minutes to Vercel  
→ Adds minimal client `authClient` to Astro  
→ Injects header buttons + modal sign-in using Better-Auth-UI  
→ Full social login working on a 100% static frontend

## Activate This Skill By Saying

- “Add Better-Auth to my project”
- “Implement signup and login with Google/Apple/Facebook/X”
- “I want Better-Auth with onboarding questions”
- “Set up authentication for my [Next.js/Astro/Remix/etc.] site”

## Available Templates

### Configuration Templates

1. **Production Auth Config v2** (`config/production-auth-v2.template.ts`)
   - Latest Better Auth v2 features
   - OAuth token encryption enabled
   - Account linking with email validation
   - Advanced security defaults

2. **Enterprise Auth Config** (`config/enterprise-auth.template.ts`)
   - Multi-tenant with organizations
   - Custom roles and permissions
   - 2FA enforcement options
   - Audit logging ready

3. **OAuth-First Config** (`config/oauth-first.template.ts`)
   - OAuth providers as primary auth
   - Account linking across providers
   - Encrypted token storage
   - Social login preferences

4. **B2B SaaS Config** (`config/b2b-saas.template.ts`)
   - Organization-based auth
   - Member invitations
   - Role hierarchy management
   - Team collaboration features

### Database Schema Templates

1. **Prisma Schema v2** (`schemas/prisma-v2.template.prisma`)
2. **Drizzle Schema v2** (`schemas/drizzle-v2.template.ts`)
3. **Kysely Schema v2** (`schemas/kysely-v2.template.ts`)
4. **MongoDB Schema** (`schemas/mongodb.template.ts`)

### Client-Side Templates

1. **React Auth Client v2** (`client/react-auth-client-v2.template.tsx`)
2. **Vue 3 Auth Client** (`client/vue3-auth-client.template.ts`)
3. **Svelte Auth Client** (`client/svelte-auth-client.template.ts`)
4. **TypeScript Auth Utilities** (`client/auth-utils.template.ts`)

### Component Templates

1. **Modern Sign In Form** (`components/SignInForm-v2.template.tsx`)
2. **Multi-Step Sign Up** (`components/SignUpFlow.template.tsx`)
3. **OAuth Provider Grid** (`components/OAuthProviderGrid.template.tsx`)
4. **2FA Setup Component** (`components/TwoFactorSetup.template.tsx`)
5. **Organization Manager** (`components/OrganizationManager.template.tsx`)
6. **Passkey Enrollment** (`components/PasskeyEnroll.template.tsx`)
7. **Session Security** (`components/SessionSecurity.template.tsx`)

### Middleware Templates

1. **Next.js App Router Middleware** (`middleware/nextjs-app-router.template.ts`)
2. **Advanced RBAC Middleware** (`middleware/rbac-gateway.template.ts`)
3. **Rate Limiting Middleware** (`middleware/rate-limiter.template.ts`)
4. **Audit Logging Middleware** (`middleware/audit-logger.template.ts`)

### Utility Templates

1. **Permission Engine** (`utils/permission-engine.template.ts`)
2. **Role Manager** (`utils/role-manager.template.ts`)
3. **Security Validator** (`utils/security-validator.template.ts`)
4. **OAuth Helper** (`utils/oauth-helper.template.ts`)

## Enhanced Features

### OAuth Token Encryption
- Automatic encryption of OAuth tokens at rest
- Secure token storage with customer-controlled encryption keys
- Token refresh without user intervention

### Account Linking
- Link multiple OAuth providers to single account
- Email verification for provider linking
- Prevent duplicate accounts with same email

### Advanced RBAC
- Hierarchical role system
- Resource-based permissions
- Time-bound role assignments
- Permission inheritance

### Multi-Tenancy
- Organization-based isolation
- Cross-organization roles
- Team-based access control
- Organization invitations

### Security Enhancements
- CSRF protection with custom tokens
- Advanced rate limiting per endpoint
- IP-based session validation
- Device fingerprinting

### 2FA Support
- TOTP (Time-based One-Time Password)
- Backup codes generation
- SMS and email 2FA
- Passkey (WebAuthn) support

---

## Quick Start Templates

### Template 1: Production Auth Configuration v2

**File**: `.claude/skills/better-auth-v2/config/production-auth-v2.template.ts`

```typescript
/**
 * Better Auth v2 - Production-Ready Configuration
 *
 * Latest Features:
 * - OAuth token encryption
 * - Account linking across providers
 * - Enhanced security defaults
 * - Performance optimizations
 *
 * Setup:
 * 1. Copy to `lib/auth.ts`
 * 2. Configure environment variables
 * 3. Set up database with schema
 * 4. Configure OAuth providers
 */

import { betterAuth } from "better-auth";
import { prismaAdapter } from "better-auth/adapters/prisma";
import { organization, twoFactor, passkey } from "better-auth/plugins";
import { PrismaClient } from "@prisma/client";

const prisma = new PrismaClient();

export const auth = betterAuth({
  // ===========================================
  // DATABASE CONFIGURATION
  // ===========================================
  database: prismaAdapter(prisma, {
    provider: "postgresql",
  }),

  // ===========================================
  // SECURITY: SECRET KEY (REQUIRED)
  // ===========================================
  secret: process.env.BETTER_AUTH_SECRET || process.env.AUTH_SECRET!,

  // ===========================================
  // BASE URL CONFIGURATION
  // ===========================================
  baseURL: process.env.BETTER_AUTH_URL || "http://localhost:3000",

  // ===========================================
  // EMAIL & PASSWORD AUTHENTICATION
  // ===========================================
  emailAndPassword: {
    enabled: true,
    requireEmailVerification: true,
    minPasswordLength: 8,
    maxPasswordLength: 128,

    // Enhanced password validation
    passwordValidation: (password) => {
      const checks = {
        length: password.length >= 8 && password.length <= 128,
        upper: /[A-Z]/.test(password),
        lower: /[a-z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>]/.test(password),
        noCommon: !password.toLowerCase().includes('password'),
        noUsername: false, // Will be checked against username/email
      };

      if (Object.values(checks).some(check => !check)) {
        return {
          valid: false,
          message: "Password must be 8-128 characters with uppercase, lowercase, number, and special character",
        };
      }

      return { valid: true };
    },

    sendEmailVerificationOnSignUp: true,
  },

  // ===========================================
  // OAUTH PROVIDERS WITH ENCRYPTION
  // ===========================================
  socialProviders: {
    github: {
      clientId: process.env.GITHUB_CLIENT_ID!,
      clientSecret: process.env.GITHUB_CLIENT_SECRET!,
      scope: ["user:email"],
      // Optional: Custom redirect URI
      // redirectURI: "https://yourapp.com/auth/callback/github"
    },

    google: {
      clientId: process.env.GOOGLE_CLIENT_ID!,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET!,
      scope: ["openid", "email", "profile"],
    },

    discord: {
      clientId: process.env.DISCORD_CLIENT_ID!,
      clientSecret: process.env.DISCORD_CLIENT_SECRET!,
      scope: ["identify", "email"],
    },

    microsoft: {
      clientId: process.env.MICROSOFT_CLIENT_ID!,
      clientSecret: process.env.MICROSOFT_CLIENT_SECRET!,
      tenant: "common",
      scope: ["openid", "email", "profile"],
    },

    // Additional providers
    /*
    apple: {
      clientId: process.env.APPLE_CLIENT_ID!,
      clientSecret: process.env.APPLE_CLIENT_SECRET!,
    },

    twitter: {
      clientId: process.env.TWITTER_CLIENT_ID!,
      clientSecret: process.env.TWITTER_CLIENT_SECRET!,
    },

    facebook: {
      clientId: process.env.FACEBOOK_CLIENT_ID!,
      clientSecret: process.env.FACEBOOK_CLIENT_SECRET!,
    },
    */
  },

  // ===========================================
  // ACCOUNT MANAGEMENT WITH ENCRYPTION
  // ===========================================
  account: {
    // Model configuration (optional)
    modelName: "accounts",
    fields: {
      userId: "user_id",
    },

    // Encrypt OAuth tokens at rest (SECURITY: Production best practice)
    encryptOAuthTokens: true,

    // Store account in cookie for database-less flows
    storeAccountCookie: false, // Set true only for specific use cases

    // Account linking configuration
    accountLinking: {
      enabled: true,
      // Trusted providers for auto-linking
      trustedProviders: ["google", "github", "microsoft", "apple"],
      // Require same email for linking
      allowDifferentEmails: false,
    },
  },

  // ===========================================
  // ENHANCED SESSION MANAGEMENT
  // ===========================================
  session: {
    expiresIn: 60 * 60 * 24 * 7, // 7 days
    updateAge: 60 * 60 * 24, // Update every 24 hours
    cookieCache: {
      enabled: true,
      maxAge: 5 * 60, // 5 minutes
    },
    // Additional session security
    sessionExpiration: {
      warning: 60 * 60 * 24, // Warn 1 day before expiration
    },
  },

  // ===========================================
  // ADVANCED SECURITY CONFIGURATION
  // ===========================================
  advanced: {
    // CSRF protection (NEVER disable in production)
    disableCSRFCheck: false,

    // Trusted origins
    trustedOrigins: [
      process.env.BETTER_AUTH_URL!,
      ...(process.env.NODE_ENV === "development"
        ? ["http://localhost:3000", "http://localhost:5173", "http://localhost:4173"]
        : []
      ),
    ],

    // Cookie security
    defaultCookieAttributes: {
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production",
      httpOnly: true,
      // Optional: Domain for cross-subdomain cookies
      // domain: ".yourdomain.com",
    },

    // Cross-subdomain cookies
    crossSubDomainCookies: {
      enabled: false, // Enable if using subdomains
      // domain: ".yourdomain.com",
    },
  },

  // ===========================================
  // RATE LIMITING WITH FINE-GRAINED CONTROL
  // ===========================================
  rateLimit: {
    enabled: true,
    window: 60, // 1 minute window
    max: 10, // 10 requests per window

    // Endpoint-specific limits
    customRules: [
      {
        pathPattern: "/api/auth/sign-in",
        window: 60,
        max: 5, // Stricter for sign-in
      },
      {
        pathPattern: "/api/auth/sign-up",
        window: 300, // 5 minutes
        max: 3, // Prevent mass sign-ups
      },
      {
        pathPattern: "/api/auth/reset-password",
        window: 900, // 15 minutes
        max: 3, // Prevent spam
      },
      {
        pathPattern: "/api/auth/verify-email",
        window: 60,
        max: 10, // Allow more attempts for verification
      },
    ],

    // IP-based rate limiting
    ipBasedLimiting: true,

    // Custom storage for rate limits (Redis recommended for production)
    // storage: customRateLimitStorage,
  },

  // ===========================================
  // USER PROFILE CONFIGURATION
  // ===========================================
  user: {
    // Additional user fields
    additionalFields: {
      displayName: {
        type: "string",
        required: false,
      },
      avatar: {
        type: "string",
        required: false,
      },
      bio: {
        type: "string",
        required: false,
      },
      preferences: {
        type: "json",
        required: false,
      },
    },

    // User model configuration
    modelName: "users",
    fields: {
      email: "email_address",
      name: "full_name",
    },
  },

  // ===========================================
  // PLUGINS FOR ENTERPRISE FEATURES
  // ===========================================
  plugins: [
    // Organization plugin for multi-tenancy
    organization({
      enabled: true,
      organizationLimit: 5, // Max organizations per user
      allowUserToCreateOrganization: true,

      // Role definitions
      roles: [
        {
          role: "owner",
          permissions: ["*"], // Full access
        },
        {
          role: "admin",
          permissions: [
            "org:*",
            "member:*",
            "billing:*",
          ],
        },
        {
          role: "member",
          permissions: [
            "org:read",
            "content:*",
          ],
        },
      ],

      // Custom application roles
      customRoles: [
        {
          role: "moderator",
          label: "Content Moderator",
          permissions: [
            "content:moderate",
            "content:delete:any",
            "user:warn",
          ],
        },
        {
          role: "analyst",
          label: "Data Analyst",
          permissions: [
            "analytics:*",
            "reports:*",
            "data:read",
          ],
        },
      ],
    }),

    // Two-factor authentication
    twoFactor({
      // Require 2FA for specific roles
      requireTwoFactorFor: ["admin", "owner"],

      // 2FA configuration
      issuer: process.env.APP_NAME || "MyApp",

      // Backup codes
      backupCodes: {
        enabled: true,
        count: 10,
      },

      // 2FA methods
      methods: ["totp", "sms", "email"],
    }),

    // Passkey (WebAuthn) support
    passkey({
      enabled: true,
      // Passkey configuration
      rpName: process.env.APP_NAME || "MyApp",
      rpID: process.env.PASSKEY_RP_ID || "localhost",
      origin: process.env.PASSKEY_ORIGIN || "http://localhost:3000",
    }),
  ],

  // ===========================================
  // EMAIL SERVICE CONFIGURATION
  // ===========================================
  emailProvider: {
    type: "smtp",
    config: {
      host: process.env.SMTP_HOST!,
      port: parseInt(process.env.SMTP_PORT || "587"),
      secure: process.env.SMTP_SECURE === "true",
      auth: {
        user: process.env.SMTP_USER!,
        pass: process.env.SMTP_PASSWORD!,
      },
    },
    from: {
      name: process.env.EMAIL_FROM_NAME || "MyApp Team",
      email: process.env.EMAIL_FROM_ADDRESS || "noreply@myapp.com",
    },

    // Email templates (optional)
    templates: {
      "email-verification": {
        subject: "Verify your email",
        text: (data) => `Click here to verify: ${data.url}`,
        html: (data) => `<a href="${data.url}">Verify Email</a>`,
      },
      "password-reset": {
        subject: "Reset your password",
        text: (data) => `Click here to reset: ${data.url}`,
        html: (data) => `<a href="${data.url}">Reset Password</a>`,
      },
    },
  },

  // ===========================================
  // WEBHOOKS (Optional)
  // ===========================================
  webhooks: {
    // User events
    onUserCreated: async (user) => {
      console.log("User created:", user.id);
      // Trigger welcome email, analytics, etc.
    },

    onUserDeleted: async (user) => {
      console.log("User deleted:", user.id);
      // Cleanup user data, revoke access tokens, etc.
    },

    // Session events
    onSignIn: async (session) => {
      console.log("User signed in:", session.userId);
      // Track login analytics
    },

    onSignOut: async (session) => {
      console.log("User signed out:", session.userId);
      // Cleanup session-specific data
    },

    // Organization events
    onOrganizationCreated: async (org) => {
      console.log("Organization created:", org.id);
      // Initialize organization settings
    },
  },

  // ===========================================
  // CUSTOM HANDLERS (Optional)
  // ===========================================
  /*
  onRequest: (request) => {
    // Custom request handling
    console.log("Auth request:", request.url);
  },

  onResponse: (response) => {
    // Custom response handling
    console.log("Auth response:", response.status);
  },

  onError: (error, context) => {
    // Custom error handling
    console.error("Auth error:", error, context);
    // Send to monitoring service
  },
  */
});

// ===========================================
// TYPE EXPORTS FOR TYPE SAFETY
// ===========================================
export type Session = typeof auth.$Infer.Session;
export type User = typeof auth.$Infer.User;
export type Organization = typeof auth.$Infer.Organization;
```

### Template 2: React Auth Client v2

**File**: `.claude/skills/better-auth-v2/client/react-auth-client-v2.template.tsx`

```typescript
/**
 * React Auth Client v2 with Enhanced Features
 *
 * Features:
 * - TypeScript integration
 * - Organization management
 * - 2FA support
 * - Passkey authentication
 * - Automatic session refresh
 * - Error boundaries
 *
 * Setup:
 * 1. Copy to `lib/auth-client.ts`
 * 2. Configure environment variables
 * 3. Use hooks in components
 */

import React, { createContext, useContext, useEffect, useState } from "react";
import { createAuthClient } from "better-auth/react";
import {
  organizationClient,
  twoFactorClient,
  passkeyClient
} from "better-auth/client";

// ===========================================
// AUTH CLIENT CONFIGURATION
// ===========================================
export const authClient = createAuthClient({
  baseURL: process.env.NEXT_PUBLIC_AUTH_URL || "http://localhost:3000",

  // Fetch options
  fetchOptions: {
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
  },

  // Enable client plugins
  plugins: [
    organizationClient({
      organizationInvitationPage: "/invite",
    }),
    twoFactorClient({
      twoFactorPage: "/2fa",
    }),
    passkeyClient(),
  ],

  // Storage configuration
  storage: {
    // Use localStorage for persistence
    mode: "localStorage",
  },

  // Session configuration
  session: {
    // Auto-refresh session
    autoRefresh: true,
    // Refresh threshold (5 minutes before expiry)
    refreshThreshold: 5 * 60,
  },
});

// ===========================================
// EXPORT AUTH METHODS
// ===========================================
export const {
  // Authentication
  useSession,
  signIn,
  signUp,
  signOut,

  // User management
  useUser,
  updateUser,

  // Password management
  forgetPassword,
  resetPassword,
  changePassword,

  // Email verification
  sendVerificationEmail,
  verifyEmail,

  // Organizations
  useActiveOrganization,
  useOrganizations,
  createOrganization,
  updateOrganization,
  deleteOrganization,
  inviteMember,
  removeMember,
  updateMemberRole,

  // 2FA
  enableTwoFactor,
  disableTwoFactor,
  verifyTwoFactor,
  generateBackupCodes,

  // Passkeys
  createPasskey,
  deletePasskey,
  usePasskeys,

  // OAuth
  listConnectedAccounts,
  unlinkAccount,
} = authClient;

// ===========================================
// REACT CONTEXT PROVIDER
// ===========================================
interface AuthContextType {
  session: Session | null;
  user: User | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  signIn: typeof signIn;
  signUp: typeof signUp;
  signOut: typeof signOut;
  refresh: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { data: session, isPending, error } = useSession();
  const [refreshing, setRefreshing] = useState(false);

  // Session refresh handler
  const refresh = React.useCallback(async () => {
    if (refreshing) return;

    setRefreshing(true);
    try {
      await authClient.getSession({
        fetchOptions: {
          headers: { "Cache-Control": "no-cache" },
        },
      });
    } catch (err) {
      console.error("Failed to refresh session:", err);
    } finally {
      setRefreshing(false);
    }
  }, [refreshing]);

  // Auto-refresh on visibility change
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (!document.hidden && session) {
        refresh();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => document.removeEventListener("visibilitychange", handleVisibilityChange);
  }, [session, refresh]);

  // Periodic session refresh
  useEffect(() => {
    if (!session) return;

    const interval = setInterval(refresh, 5 * 60 * 1000); // 5 minutes
    return () => clearInterval(interval);
  }, [session, refresh]);

  const contextValue: AuthContextType = {
    session,
    user: session?.user || null,
    isLoading: isPending || refreshing,
    error: error?.message || null,

    signIn,
    signUp,
    signOut,
    refresh,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

// ===========================================
// CUSTOM HOOKS
// ===========================================

/**
 * Use auth context
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}

/**
 * Check if user is authenticated
 */
export function useIsAuthenticated() {
  const { session, isLoading } = useAuth();
  return { isAuthenticated: !!session, isLoading };
}

/**
 * Require authentication (with redirect)
 */
export function useRequireAuth(redirectTo: string = "/signin") {
  const { isAuthenticated, isLoading } = useIsAuthenticated();
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, isLoading, router, redirectTo]);

  return { isAuthenticated, isLoading };
}

/**
 * Check user permissions
 */
export function usePermissions(permissions: string | string[]) {
  const { session } = useAuth();
  const [userPermissions, setUserPermissions] = useState<string[]>([]);

  useEffect(() => {
    if (!session?.user) {
      setUserPermissions([]);
      return;
    }

    // Get user permissions based on role
    const getPermissions = async () => {
      try {
        const response = await fetch("/api/auth/permissions", {
          credentials: "include",
        });
        const data = await response.json();
        setUserPermissions(data.permissions || []);
      } catch (err) {
        console.error("Failed to fetch permissions:", err);
        setUserPermissions([]);
      }
    };

    getPermissions();
  }, [session]);

  const requiredPermissions = Array.isArray(permissions) ? permissions : [permissions];
  const hasPermissions = requiredPermissions.every(p =>
    userPermissions.includes(p) || userPermissions.includes("*")
  );

  return { hasPermissions, permissions: userPermissions };
}

/**
 * Require specific permissions
 */
export function useRequirePermissions(
  permissions: string | string[],
  redirectTo: string = "/unauthorized"
) {
  const { hasPermissions, isLoading } = usePermissions(permissions);
  const router = useRouter();

  useEffect(() => {
    if (!isLoading && !hasPermissions) {
      router.push(redirectTo);
    }
  }, [hasPermissions, isLoading, router, redirectTo]);

  return { hasPermissions, isLoading };
}

/**
 * Organization management
 */
export function useOrganization(orgId?: string) {
  const [organization, setOrganization] = useState<Organization | null>(null);
  const [members, setMembers] = useState<Member[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchOrganization = async () => {
      try {
        const [orgData, membersData] = await Promise.all([
          fetch(`/api/organizations/${orgId || "current"}`, {
            credentials: "include",
          }),
          fetch(`/api/organizations/${orgId || "current"}/members`, {
            credentials: "include",
          }),
        ]);

        const org = await orgData.json();
        const memberList = await membersData.json();

        setOrganization(org);
        setMembers(memberList);
      } catch (err) {
        console.error("Failed to fetch organization:", err);
      } finally {
        setIsLoading(false);
      }
    };

    if (orgId || organization) {
      fetchOrganization();
    }
  }, [orgId, organization]);

  return { organization, members, isLoading };
}

/**
 * 2FA status
 */
export function useTwoFactor() {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isVerified, setIsVerified] = useState(false);
  const [backupCodes, setBackupCodes] = useState<string[]>([]);

  useEffect(() => {
    const fetch2FAStatus = async () => {
      try {
        const response = await fetch("/api/auth/2fa/status", {
          credentials: "include",
        });
        const data = await response.json();

        setIsEnabled(data.enabled);
        setIsVerified(data.verified);
      } catch (err) {
        console.error("Failed to fetch 2FA status:", err);
      }
    };

    fetch2FAStatus();
  }, []);

  const enable = async () => {
    const result = await enableTwoFactor();
    if (result.data) {
      setIsEnabled(true);
      if (result.data.backupCodes) {
        setBackupCodes(result.data.backupCodes);
      }
    }
    return result;
  };

  const disable = async () => {
    const result = await disableTwoFactor();
    if (result.data) {
      setIsEnabled(false);
      setIsVerified(false);
      setBackupCodes([]);
    }
    return result;
  };

  return {
    isEnabled,
    isVerified,
    backupCodes,
    enable,
    disable,
    generateBackupCodes,
  };
}

/**
 * Passkey management
 */
export function usePasskeyAuth() {
  const { data: passkeys, isLoading } = usePasskeys();
  const [isSupported, setIsSupported] = useState(false);

  useEffect(() => {
    // Check if WebAuthn is supported
    setIsSupported(!!window.PublicKeyCredential);
  }, []);

  const addPasskey = async (name: string) => {
    return await createPasskey({
      name,
      options: {
        authenticatorSelection: {
          userVerification: "required",
          residentKey: "preferred",
        },
      },
    });
  };

  const removePasskey = async (passkeyId: string) => {
    return await deletePasskey(passkeyId);
  };

  return {
    passkeys: passkeys || [],
    isLoading,
    isSupported,
    addPasskey,
    removePasskey,
  };
}

// ===========================================
// UTILITY FUNCTIONS
// ===========================================

/**
 * Format user display name
 */
export function formatUserName(user: User): string {
  if (user.name) return user.name;
  if (user.displayName) return user.displayName;
  return user.email.split("@")[0];
}

/**
 * Get user initials
 */
export function getUserInitials(user: User): string {
  const name = formatUserName(user);
  return name
    .split(" ")
    .map(word => word[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

/**
 * Validate session activity
 */
export function isSessionActive(session: Session | null): boolean {
  if (!session) return false;

  const now = new Date();
  const expires = new Date(session.expiresAt);

  // Check if session expires within 5 minutes
  const fiveMinutesFromNow = new Date(now.getTime() + 5 * 60 * 1000);
  return expires > fiveMinutesFromNow;
}

// ===========================================
// TYPE EXPORTS
// ===========================================
export type Session = Awaited<ReturnType<typeof useSession>>["data"];
export type User = NonNullable<Session>["user"];
export type Organization = Awaited<ReturnType<typeof useOrganizations>>["data"]?.[0];
export type Member = Awaited<ReturnType<typeof removeMember>>["data"];
```

## Getting Started

1. **Install Dependencies**
   ```bash
   npm install better-auth@latest @better-auth/prisma-adapter
   ```

2. **Set Up Database**
   - Choose your adapter (Prisma, Drizzle, Kysely, or MongoDB)
   - Copy and run the appropriate schema template
   - Run migrations

3. **Configure Auth**
   - Copy the production configuration template
   - Set up environment variables
   - Configure OAuth providers

4. **Set Up Client**
   - Copy the React client template
   - Wrap your app with `AuthProvider`
   - Use hooks in components

5. **Add Components**
   - Copy authentication component templates
   - Customize for your application
   - Add to your pages

## Environment Variables

Create a `.env.local` file with:

```env
# Core Auth
BETTER_AUTH_SECRET=your-secret-key-here
BETTER_AUTH_URL=http://localhost:3000

# Database
DATABASE_URL=your-database-url

# OAuth Providers
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# Email Service
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_SECURE=false
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM_ADDRESS=noreply@example.com
EMAIL_FROM_NAME=Your App

# App Settings
APP_NAME=Your App Name
PASSKEY_RP_ID=yourdomain.com
PASSKEY_ORIGIN=https://yourdomain.com
```

## Security Checklist

- [ ] Set strong, unique `BETTER_AUTH_SECRET`
- [ ] Enable OAuth token encryption
- [ ] Configure rate limiting
- [ ] Set up proper CORS origins
- [ ] Enable 2FA for sensitive roles
- [ ] Configure email verification
- [ ] Set up audit logging
- [ ] Review session settings
- [ ] Test password reset flow
- [ ] Verify OAuth callback URLs

## ⚠️ Critical Implementation Lessons Learned

Based on real-world OAuth implementation challenges, avoid these common pitfalls:

### 1. Database Schema Conflicts
**Problem**: Using reserved attribute names like `metadata` in SQLAlchemy models
```python
# ❌ Causes error
class ChatMessage(Base):
    metadata = Column(JSON, nullable=True)  # SQLAlchemy reserves this!

# ✅ Fixed version
class ChatMessage(Base):
    message_metadata = Column(JSON, nullable=True)  # Use different name
```

### 2. OAuth Redirect URI Configuration
**Critical Issues**:
- Always include the full path with trailing slash removal
- For cross-platform deployments (GitHub Pages + HuggingFace):
  ```env
  # OAuth callback to backend
  AUTH_REDIRECT_URI=https://your-hf-space.hf.space/backend/auth/google/callback
  # Frontend redirect after auth
  FRONTEND_URL=https://your-username.github.io/your-repo
  ```

### 3. Session Middleware Requirements
**Must-Have**: OAuth requires SessionMiddleware for state parameter
```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.jwt_secret_key,
    session_cookie="session_id",
    max_age=3600,
    same_site="lax",
    https_only=False,  # Set true in production
)
```

### 4. Docusaurus Base Path Handling
**Issue**: Static sites have base paths that affect OAuth callbacks
```typescript
// Docusaurus config
baseUrl: '/ai-humanoid-robotics/',  // This affects ALL routes

// Must match in environment
FRONTEND_URL=https://username.github.io/ai-humanoid-robotics
```

### 5. Google OAuth Response Structure
**Problem**: Provider account ID (`sub`) field might be missing
```python
def create_or_update_account(db: Session, user: User, provider: str, account_info: dict) -> Account:
    provider_account_id = account_info.get('sub')  # Primary: Google ID
    if not provider_account_id:
        # Fallback to email
        provider_account_id = account_info.get('email')
    if not provider_account_id:
        # Final fallback
        provider_account_id = str(user.id)
```

### 6. GitHub Pages Static Route Handling
**Problem**: Cannot create dynamic routes on static sites
```typescript
// Create static page: src/pages/auth/callback.tsx
export default function AuthCallbackPage() {
  return <OAuthCallbackHandler />;
}
```

### 7. Dependency Management
**Missing Dependencies Cause Failures**:
```toml
# pyproject.toml
dependencies = [
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "python-jose[cryptography]>=3.3.0",
    "authlib>=1.2.1",
    "itsdangerous>=2.1.0",  # Required for SessionMiddleware
]
```

### 8. CORS Configuration Checklist
**Essential for Cross-Platform**:
```python
# main.py
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://username.github.io",
    "https://huggingface.co",
    "https://your-hf-space.hf.space",
]
```

### 9. JWT Secret Key Requirements
**Must Configure**:
```python
class Settings(BaseSettings):
    # Add to your settings class
    jwt_secret_key: str = "your-super-secret-jwt-key-at-least-32-characters-long"
```

### 10. Production Deployment Checklist
- [ ] Test OAuth in production environment (localhost may work with wrong URLs)
- [ ] Verify redirect URIs match EXACTLY in provider console
- [ ] Include base path in frontend URLs for static sites
- [ ] Set up proper session middleware before OAuth routes
- [ ] Configure CORS for all deployment domains
- [ ] Enable HTTPS in production
- [ ] Set proper cookie attributes (SameSite, Secure, HttpOnly)

## Next Steps

1. Customize the templates for your application
2. Set up additional OAuth providers as needed
3. Configure advanced RBAC rules
4. Set up monitoring and analytics
5. Add custom email templates
6. Configure webhooks for your business logic
7. **Review the lessons learned above to avoid common pitfalls**

For detailed documentation and advanced configurations, visit the [Better Auth documentation](https://better-auth.com/docs).

---

## FastAPI + React JWT Authentication: Critical Implementation Lessons

**Context**: These lessons are from implementing JWT-based authentication with FastAPI (backend) and React (frontend), not using Better Auth library. If you're implementing custom JWT authentication, avoid these pitfalls:

### 1. Database Column Name Mismatches

**Problem**: SQLAlchemy model attribute names don't always match database column names
```python
# ❌ This causes error: "column user_backgrounds.years_of_experience does not exist"
class UserBackground(Base):
    years_of_experience = Column(Integer, nullable=False, default=0)

# ✅ Fix: Add explicit column name mapping
class UserBackground(Base):
    years_of_experience = Column("years_experience", Integer, nullable=False, default=0)
```

**Root Cause**: Database migration created `years_experience` column but model uses `years_of_experience` attribute name. SQLAlchemy needs explicit column name when they differ.

**Files**: `backend/src/models/auth.py`

---

### 2. Async Database Operations with asyncpg Driver

**Problem**: Using synchronous SQLAlchemy with async PostgreSQL driver causes connection errors
```python
# ❌ This causes: "TypeError: connect() got an unexpected keyword argument 'sslmode'"
from src.database.base import get_db  # Synchronous session

@router.get("/background")
async def get_user_background(db = Depends(get_db)):
    result = db.query(UserBackground).filter(...).first()  # Sync query
```

**✅ Fix: Use AsyncSession with async queries**
```python
from src.core.database import get_async_db  # Async session
from sqlalchemy import select

@router.get("/background")
async def get_user_background(
    request: Request,
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.execute(
        select(UserBackground).where(UserBackground.user_id == user.id)
    )
    background = result.scalar_one_or_none()
    await db.commit()
```

**Root Cause**: asyncpg driver doesn't support synchronous connection parameters. All database operations must be async.

**Files**: `backend/src/api/routes/users.py`

---

### 3. useReducer Lazy Initialization with localStorage

**Problem**: Initial state evaluated at module load time when localStorage is unavailable
```typescript
// ❌ This runs at module load, localStorage might not be available
const initialState: AuthState = {
  token: localStorage.getItem('auth_token'),  // Can be null or error
  isLoading: !!localStorage.getItem('auth_token'),
  // ...
};

const [state, dispatch] = useReducer(authReducer, initialState);
```

**✅ Fix: Use lazy initialization with init function**
```typescript
// Function called when component mounts, not at module load
const getInitialState = (): AuthState => {
  const tokens = tokenManager.getTokens();  // Safely called after mount
  console.log('[AuthContext] getInitialState:', {
    hasToken: !!tokens.token,
    isLoading: !!tokens.token
  });
  return {
    user: null,
    token: tokens.token,
    refreshToken: tokens.refreshToken,
    isLoading: !!tokens.token,  // Only load if token exists
    isAuthenticated: false,
    error: null,
  };
};

const [state, dispatch] = useReducer(authReducer, undefined, getInitialState);
```

**Root Cause**: React's `useReducer` with lazy initialization (third parameter) defers initial state calculation until component mount, ensuring browser APIs are available.

**Files**: `src/context/AuthContext.tsx`

---

### 4. Reducer Actions Must Update All State

**Problem**: Missing state updates in reducer causes infinite loading
```typescript
// ❌ isLoading never gets reset to false
case 'SET_USER':
  return {
    ...state,
    user: action.payload,
    isAuthenticated: true,
    // Missing: isLoading: false
  };
```

**✅ Fix: Always update isLoading in auth state changes**
```typescript
case 'SET_USER':
  return {
    ...state,
    user: action.payload,
    isAuthenticated: true,
    isLoading: false,  // CRITICAL: Reset loading state
  };
```

**Root Cause**: Components waiting for `isLoading` to become `false` will hang forever.

**Files**: `src/context/AuthContext.tsx`

---

### 5. API Response Format Consistency

**Problem**: Different endpoints return different response structures
```typescript
// ❌ /api/v1/auth/register returns:
{ success: true, user: {...}, token: "..." }

// But /api/v1/auth/me returns user directly:
{ id: "...", email: "...", name: "..." }
```

**✅ Fix: Handle both response formats in frontend**
```typescript
// Check response format appropriately
if (response.success && response.user && response.token) {
  // Register/Login response
  tokenManager.setTokens(response.token, response.refreshToken);
  dispatch({ type: 'AUTH_SUCCESS', payload: response });
} else if (response && response.id) {
  // Direct user response from /me endpoint
  dispatch({ type: 'SET_USER', payload: response });
}
```

**Better Solution**: Standardize all endpoint responses
```python
# Backend: Always use consistent wrapper
class UserResponse(BaseModel):
    success: bool
    user: Dict[str, Any]  # Use Dict for camelCase flexibility
    token: Optional[str] = None
```

**Files**: `src/context/AuthContext.tsx`, `backend/src/api/v1/auth.py`

---

### 6. Token Storage Key Consistency

**Problem**: Different parts of codebase use different localStorage keys
```typescript
// ❌ Inconsistent key names
localStorage.getItem('access_token')    // api.ts
localStorage.setItem('auth_token', ...) // auth-api.ts
localStorage.getItem('token')           // Some other file
```

**✅ Fix: Standardize on one key name across entire app**
```typescript
// Create a centralized token manager
class TokenManager {
  private readonly TOKEN_KEY = 'auth_token';
  private readonly REFRESH_KEY = 'refresh_token';

  getTokens() {
    return {
      token: localStorage.getItem(this.TOKEN_KEY),
      refreshToken: localStorage.getItem(this.REFRESH_KEY)
    };
  }

  setTokens(token: string, refreshToken?: string) {
    localStorage.setItem(this.TOKEN_KEY, token);
    if (refreshToken) {
      localStorage.setItem(this.REFRESH_KEY, refreshToken);
    }
  }
}
```

**Files**: `src/services/auth-api.ts`, `src/services/api.ts`

---

### 7. Race Conditions in Auth Check

**Problem**: Components initialize before authentication check completes
```typescript
// ❌ Initializes anonymous session before knowing if user is authenticated
const { isAuthenticated } = useAuth();

useEffect(() => {
  if (!isAuthenticated) {
    initializeAnonymousSession();  // Runs too early!
  }
}, [isAuthenticated]);
```

**✅ Fix: Wait for auth check to complete before taking action**
```typescript
const { isAuthenticated, isLoading } = useAuth();  // Include isLoading

useEffect(() => {
  // Only initialize if not authenticated AND auth check is complete
  if (!isAuthenticated && !isLoading) {
    initializeAnonymousSession();
  }
}, [isAuthenticated, isLoading]);  // Both as dependencies
```

**Root Cause**: `isLoading` indicates auth check is in progress. Components must wait for `isLoading: false` before making auth-dependent decisions.

**Files**: `src/components/ChatWidget/ChatWidgetContainer.tsx`

---

### 8. Middleware User vs Dependency Injection

**Problem**: Inconsistent user retrieval patterns across endpoints
```python
# ❌ Old way: Duplicate authentication logic
@router.get("/background")
async def get_background(
    current_user: User = Depends(get_current_active_user)
):
    # Re-validates token, makes extra DB query
    pass

# ✅ New way: Use middleware's validated user
@router.get("/background")
async def get_background(request: Request):
    user = request.state.user  # Already validated by middleware
    pass
```

**Benefits**:
- Middleware validates token once per request
- Reduces database queries
- Consistent authentication across all endpoints

**Files**: `backend/src/api/routes/users.py`, `backend/middleware/auth.py`

---

### 9. Module Import Path Updates

**Problem**: Refactoring breaks imports across codebase
```python
# ❌ Old import after code reorganization
from auth.auth import verify_token

# ✅ Fix: Update to new module path
from src.core.security import verify_token
```

**Best Practice**: When refactoring, use IDE's "Find All References" to update all imports consistently.

**Files**: `backend/middleware/auth.py`

---

### 10. Missing Dependencies

**Problem**: Required packages not installed, causing cryptic errors
```
ModuleNotFoundError: No module named 'sqlmodel'
ModuleNotFoundError: No module named 'psycopg2'
```

**✅ Fix: Install all required dependencies upfront**
```bash
# Database dependencies
pip install sqlalchemy[asyncio] asyncpg psycopg2-binary

# ORM dependencies
pip install sqlmodel

# Auth dependencies
pip install python-jose[cryptography] passlib[bcrypt]
```

**Files**: `backend/pyproject.toml` or `requirements.txt`

---

### Quick Reference: JWT Auth Implementation Checklist

**Backend (FastAPI)**:
- [ ] Use `AsyncSession` with async database driver (asyncpg)
- [ ] Add explicit column name mappings for model attributes
- [ ] Implement middleware for consistent authentication
- [ ] Standardize API response formats (wrapper or direct)
- [ ] Install all dependencies: `sqlalchemy[asyncio]`, `asyncpg`, `python-jose`, `passlib`

**Frontend (React)**:
- [ ] Use `useReducer` with lazy initialization for localStorage-dependent state
- [ ] Always update `isLoading` in all auth reducer actions
- [ ] Include `isLoading` in auth-dependent conditional logic
- [ ] Standardize token storage keys across entire app
- [ ] Handle both wrapped and direct API response formats

**Testing**:
- [ ] Test page refresh with valid token (should stay logged in)
- [ ] Test page refresh with expired token (should log out)
- [ ] Test authenticated endpoints with valid token
- [ ] Test authenticated endpoints without token (should return 401)
- [ ] Test async database operations don't block requests

**Common Error Messages and Solutions**:

| Error | Root Cause | Solution |
|-------|-----------|----------|
| `column ... does not exist` | Model attribute != DB column name | Add explicit column name mapping |
| `TypeError: connect() got an unexpected keyword argument 'sslmode'` | Sync SQLAlchemy with async driver | Convert to async operations |
| `User logs out on refresh` | Multiple: isLoading not reset, lazy init issue, race condition | Check all three fixes above |
| `LocalStorage token: None` | Wrong storage key | Standardize key names |
| `401 Unauthorized` on valid token | Import path issues, middleware not loading | Update imports, verify middleware order |