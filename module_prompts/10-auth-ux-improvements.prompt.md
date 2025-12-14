# Module 10: Authentication and UX Improvements Implementation

## Overview
Implement critical improvements to guest session persistence, authentication flow, knowledge collection during registration, navigation updates, and message limit notifications to enhance user experience and retention.

## Context
Based on user feedback and production experience, we need to fix several UX issues:
1. Guest users lose their message count on page refresh
2. Authenticated users get logged out after refresh
3. User knowledge/background is collected post-registration instead of during
4. Course navigation uses "Part X" instead of "Module X"
5. Message limit warnings need better timing and visibility

## Implementation Plan

### Phase 1: Guest Session Persistence (Priority: High)

#### Backend Tasks
1. **Create anonymous session endpoint** in `backend/src/api/routes/auth.py`:
   ```python
   @router.get("/anonymous-session/{session_id}")
   async def get_anonymous_session(
       session_id: str,
       db: Session = Depends(get_db)
   ) -> dict:
       # Fetch session from database
       # Return message_count, created_at, last_activity
       # Handle expired sessions (24-hour timeout)
   ```

2. **Import necessary models**:
   - Add `AnonymousSession` import to the auth routes
   - Check if `AnonymousSession` model exists in `backend/src/models/auth.py`
   - Create model if it doesn't exist

#### Frontend Tasks
1. **Update ChatWidgetContainer.tsx**:
   - Add useEffect to fetch session data on component mount
   - Use existing `anonymous_session_id` from localStorage
   - Handle API response and update state

2. **Update ChatInterface.tsx**:
   - Initialize messageCount from fetched session data
   - Ensure state persistence across page refreshes

### Phase 2: Authentication Persistence (Priority: High)

1. **Fix AuthContext.tsx**:
   - Ensure `checkAuth()` runs immediately on app initialization
   - Fix token retrieval from localStorage
   - Add proper error handling for expired tokens
   - Use `useEffect` with empty dependency array to run on mount

2. **Update app initialization**:
   - Check if AuthContext wraps the app in `src/theme/Root.tsx`
   - Add loading state during initial auth check

### Phase 3: Knowledge Collection During Registration (Priority: Medium)

#### Frontend Tasks
1. **Create RegistrationForm.tsx** in `src/components/Auth/`:
   ```tsx
   interface RegistrationData {
     email: string;
     password: string;
     name: string;
     software_experience: 'Beginner' | 'Intermediate' | 'Advanced';
     hardware_expertise: 'None' | 'Arduino' | 'ROS-Pro';
     years_of_experience: number;
   }
   ```

2. **Enhance LoginButton.tsx**:
   - Add toggle between login and registration forms
   - Include knowledge collection fields in registration
   - Maintain clean UI with progressive disclosure

#### Backend Tasks
1. **Update registration schema** in `backend/src/schemas/auth.py`:
   - Add optional fields for background data
   - Create `UserCreateWithBackground` schema

2. **Modify registration endpoint**:
   - Accept background data in `/auth/register`
   - Create UserBackground record upon registration
   - Make fields optional for backward compatibility

3. **Update AuthContext**:
   - Pass background data in register() method
   - Handle new registration form structure

### Phase 4: Navigation Updates (Priority: Low)

1. **Update sidebar configuration** in `sidebars.ts`:
   - Change all "Part X" labels to "Module X"
   - **IMPORTANT**: Change `collapsed: true` to `collapsed: false` for Module 1
   - Update category structure accordingly

2. **Update all document content**:
   - Global search and replace "Part X" with "Module X"
   - Update headers, references, and cross-links
   - Focus on MDX files in `docs/` directories

3. **Add mobile sidebar drawer**:
   - **Restore sidebar in mobile drawer** - it was accidentally removed
   - The mobile drawer should include the course index sidebar
   - Ensure the sidebar is accessible via hamburger menu on mobile
   - Check if the sidebar is properly configured in the Docusaurus theme

4. **Hide specific header elements on mobile**:
   - Hide GitHub link in header on mobile devices
   - Hide "Read Book" link in header on mobile devices
   - Add CSS in `src/css/custom.css`:
     ```css
     @media (max-width: 996px) {
       .navbar__items--right .navbar__link[href*="github"],
       .navbar__items--right .navbar__link[href*="/docs"] {
         display: none !important;
       }
     }
     ```

5. **Verify Docusaurus config**:
   - Ensure `autoCollapseCategories: true` is set
   - Confirm sidebar references are correct
   - Check navbar configuration for responsive behavior

### Phase 5: Message Limit Notifications (Priority: Medium)

1. **Update notification logic** in `src/components/ChatWidget/components/ChatInterface.tsx`:
   - Show warning banner after 2nd message (not 3rd)
   - Display "You have 1 message remaining"
   - Update useEffect message count tracking

2. **Enhance AuthenticationBanner.tsx**:
   - Add dynamic messaging based on remaining messages
   - Improve styling for better visibility
   - Ensure clear CTA when limit approached

3. **Optional: Add visual counter**:
   - Display "2/3 messages used" for guests
   - Update in real-time as messages are sent
   - Position near input area for visibility

## Implementation Order

1. **Start with Phase 1** (Guest Session Persistence) - affects UX immediately
2. **Move to Phase 2** (Authentication Persistence) - critical for retention
3. **Implement Phase 5** (Message Notifications) - quick UX win
4. **Complete Phase 3** (Knowledge Collection) - data for personalization
5. **Finish with Phase 4** (Navigation Updates) - content improvements

## Testing Requirements

- [ ] Guest session persists across page refresh (verify with browser refresh)
- [ ] User stays logged in after refresh and browser restart
- [ ] Registration captures all background fields correctly
- [ ] Message limit warning appears after 2nd message with "1 remaining"
- [ ] Navigation displays "Module X" consistently
- [ ] Module 1 sidebar is **expanded** by default (not collapsed)
- [ ] **Mobile sidebar drawer shows course index** (accessed via hamburger menu)
- [ ] **GitHub link is hidden on mobile devices**
- [ ] **"Read Book" link is hidden on mobile devices**
- [ ] All features work on desktop and mobile
- [ ] No console errors in browser dev tools
- [ ] Test mobile responsiveness using Chrome DevTools device emulation

## Important Notes

1. **LocalStorage Strategy**: Anonymous session ID should persist in localStorage
2. **Error Handling**: Graceful degradation when API calls fail
3. **Backward Compatibility**: All new fields should be optional
4. **Mobile UX**: Ensure all changes work well on mobile devices
5. **Performance**: Minimize additional API calls on page load

## Files to Modify

### Frontend
- `src/components/ChatWidget/ChatWidgetContainer.tsx`
- `src/components/ChatWidget/components/ChatInterface.tsx`
- `src/contexts/AuthContext.tsx`
- `src/components/Auth/LoginButton.tsx`
- `src/components/Auth/AuthenticationBanner.tsx`
- `src/components/Auth/RegistrationForm.tsx` (new)
- `sidebars.ts`
- `docusaurus.config.ts` (for mobile navbar configuration)
- `src/css/custom.css` (for mobile responsive styles)
- All MDX files in `docs/` folders

### Backend
- `backend/src/api/routes/auth.py`
- `backend/src/models/auth.py`
- `backend/src/schemas/auth.py`

## Success Metrics

1. Reduced bounce rate for guest users (they can continue conversation after refresh)
2. Improved user retention (staying logged in)
3. Complete user profiles with background data
4. Clearer navigation structure
5. Better conversion from guest to registered user

## Risks and Mitigations

1. **Session Data Loss**: If localStorage cleared, create new session
2. **Token Expiration**: Handle gracefully with re-login prompt
3. **Registration Friction**: Make background fields optional with "Skip for now"
4. **Content Inconsistency**: Test all navigation links after updates

## Next Steps

1. Begin with Phase 1 implementation
2. Test each phase thoroughly before proceeding
3. Gather user feedback on implemented changes
4. Monitor analytics for improvements in user engagement