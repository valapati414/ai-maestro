# AI-MAESTRO Code Review - 2026-05-24

## Skills.sh Installation

- Installed skill package source: `vercel-labs/agent-skills`
- Installed skill: `vercel-react-best-practices`
- Install target: project scope for `GitHub Copilot`
- Installed path: `.agents/skills/vercel-react-best-practices`

Command used:

```bash
npx -y skills add vercel-labs/agent-skills --skill vercel-react-best-practices --agent github-copilot -y
```

Verification:

```bash
npx -y skills list --json
```

## Review Scope

Automated checks run:

- `yarn lint`
- `./node_modules/.bin/tsc --noEmit`
- `yarn test`

## Issues Found and Status

### Fixed

1. **TypeScript test compile failure**
   - File: `tests/tmux-capture.test.ts`
   - Symptom: `TS2304: Cannot find name 'beforeEach'`
   - Cause: `beforeEach` was used but not imported from `vitest`.
   - Fix: Added `beforeEach` to the vitest import list.
   - Status: ✅ Resolved (`tsc --noEmit` now passes)

2. **Accessibility attribute misuse in compose recipient input**
   - File: `components/MessageCenter.tsx`
   - Symptom: `jsx-a11y/role-supports-aria-props`
   - Cause: `aria-expanded` was applied to a plain text input (`textbox`), where that attribute is not supported.
   - Fix: Removed invalid `aria-expanded` from the input.
   - Status: ✅ Resolved (warning no longer present)

### Remaining Lint Warnings (Technical Debt)

- Total warnings: **64**
- Breakdown by rule:
  - `react-hooks/exhaustive-deps`: 32
  - `@next/next/no-img-element`: 32

> These are non-blocking warnings (no build/test/type-check failure), but they should be addressed in a follow-up sweep.

## Complete Warning Inventory (All Remaining Issues)

- ./app/companion/page.tsx:124:6 - 124:6React Hook useEffect has a missing dependency: 'activeAgentId'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./app/companion/page.tsx:358:6 - 358:6React Hook useEffect has a missing dependency: 'activeAgent.hostId'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./app/companion/page.tsx:410:13 - 410:13Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./app/companion/page.tsx:617:27 - 617:27Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./app/companion/page.tsx:649:11 - 649:11Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./app/companion/page.tsx:908:21 - 908:21Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./app/companion/page.tsx:1004:29 - 1004:29Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./app/immersive/page.tsx:232:6 - 232:6React Hook useEffect has a missing dependency: 'activeAgent.hostId'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./app/zoom/agent/page.tsx:108:23 - 108:23Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./app/zoom/page.tsx:364:25 - 364:25Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AMPAddressesSection.tsx:53:6 - 53:6React Hook useEffect has a missing dependency: 'fetchAddresses'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/AgentBadge.tsx:341:15 - 341:15Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AgentCreationWizard.tsx:535:15 - 535:15Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AgentCreationWizard.tsx:752:11 - 752:11Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AgentGraph.tsx:296:6 - 296:6React Hook useEffect has missing dependencies: 'detectProjectPath', 'fetchGraphData', and 'fetchStats'. Either include them or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/AgentList.tsx:824:27 - 824:27Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AgentList.tsx:1305:47 - 1305:47Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AgentProfile.tsx:111:6 - 111:6React Hook useEffect has a missing dependency: 'baseUrl'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/AgentProfile.tsx:134:6 - 134:6React Hook useEffect has a missing dependency: 'baseUrl'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/AgentProfile.tsx:427:27 - 427:27Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/AvatarPicker.tsx:163:19 - 163:19Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/ConversationDetailPanel.tsx:76:6 - 76:6React Hook useEffect has a missing dependency: 'loadConversation'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/ConversationDetailPanel.tsx:484:6 - 484:6React Hook useEffect has a missing dependency: 'performSemanticSearch'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/ConversationDetailPanel.tsx:494:9 - 494:9The 'matchIndices' conditional could make the dependencies of useEffect Hook (at line 555) change on every render. To fix this, wrap the initialization of 'matchIndices' in its own useMemo() Hook.  react-hooks/exhaustive-deps
- ./components/CreateAgentAnimation.tsx:350:11 - 350:11Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/CreateAgentAnimation.tsx:457:13 - 457:13Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/DocumentationPanel.tsx:160:6 - 160:6React Hook useEffect has missing dependencies: 'fetchDocuments' and 'fetchStats'. Either include them or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/EmailAddressDialog.tsx:76:6 - 76:6React Hook useEffect has a missing dependency: 'fetchDomains'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/EmailAddressesSection.tsx:55:6 - 55:6React Hook useEffect has a missing dependency: 'fetchAddresses'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MemoryViewer.tsx:209:6 - 209:6React Hook useEffect has missing dependencies: 'fetchMemories' and 'fetchStats'. Either include them or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MemoryViewer.tsx:216:6 - 216:6React Hook useEffect has a missing dependency: 'fetchGraph'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MemoryViewer.tsx:810:6 - 810:6React Hook useEffect has a missing dependency: 'nodes.length'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MemoryViewer.tsx:810:13 - 810:13React Hook useEffect has a complex expression in the dependency array. Extract it to a separate variable so it can be statically checked.  react-hooks/exhaustive-deps
- ./components/MessageCenter.tsx:384:6 - 384:6React Hook useEffect has missing dependencies: 'fetchMessages', 'fetchSentCount', 'fetchSentMessages', and 'fetchUnreadCount'. Either include them or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MessageCenter.tsx:396:6 - 396:6React Hook useEffect has missing dependencies: 'fetchMessages', 'fetchSentCount', 'fetchSentMessages', and 'fetchUnreadCount'. Either include them or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileCallOverlay.tsx:38:6 - 38:6React Hook useCallback has a missing dependency: 'tts'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileCallOverlay.tsx:66:6 - 66:6React Hook useEffect has a missing dependency: 'tts'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileCallOverlay.tsx:95:6 - 95:6React Hook useCallback has a missing dependency: 'tts'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileCallOverlay.tsx:138:15 - 138:15Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/MobileCallOverlay.tsx:172:11 - 172:11Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/MobileCallOverlay.tsx:201:17 - 201:17Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/MobileCallOverlay.tsx:223:15 - 223:15Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/MobileConversationDetail.tsx:87:6 - 87:6React Hook useEffect has a missing dependency: 'loadConversation'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileHostsList.tsx:166:6 - 166:6React Hook useMemo has a missing dependency: 'getHostName'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileKeyToolbar.tsx:90:6 - 90:6React Hook useCallback has a missing dependency: 'stopRepeat'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/MobileWorkTree.tsx:260:6 - 260:6React Hook useEffect has a missing dependency: 'fetchWorkTree'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/TabletDashboard.tsx:177:21 - 177:21Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/TerminalView.tsx:462:6 - 462:6React Hook useCallback has a missing dependency: 'addToast'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/TransferAgentDialog.tsx:101:6 - 101:6React Hook useEffect has a missing dependency: 'baseUrl'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/WorkTree.tsx:219:6 - 219:6React Hook useEffect has a missing dependency: 'fetchWorkTree'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/marketplace/SkillDetailModal.tsx:55:6 - 55:6React Hook useEffect has a missing dependency: 'loadSkillContent'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/onboarding/FirstAgentWizard.tsx:121:15 - 121:15Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/onboarding/UseCaseSelector.tsx:79:17 - 79:17Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/settings/HostsSection.tsx:146:6 - 146:6React Hook useEffect has a missing dependency: 'refreshAllHosts'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/sidebar/TeamCard.tsx:56:19 - 56:19Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/sidebar/TeamListView.tsx:238:25 - 238:25Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/team-meeting/AgentPicker.tsx:75:21 - 75:21Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/team-meeting/MeetingSidebar.tsx:198:23 - 198:23Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/team-meeting/MeetingSidebar.tsx:311:21 - 311:21Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/team-meeting/MeetingTerminalArea.tsx:20:5 - 20:5React Hook useMemo has a missing dependency: 'activeAgent'. Either include it or remove the dependency array.  react-hooks/exhaustive-deps
- ./components/team-meeting/RingingAnimation.tsx:122:23 - 122:23Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/team-meeting/SelectedAgentsBar.tsx:52:23 - 52:23Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/zoom/AgentCard.tsx:128:15 - 128:15Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
- ./components/zoom/AgentProfileTab.tsx:322:21 - 322:21Using `<img>` could result in slower LCP and higher bandwidth. Consider using `<Image />` from `next/image` to automatically optimize images. This may incur additional usage or cost from your provider. See: https://nextjs.org/docs/messages/no-img-element  @next/next/no-img-element
