# Accord PDF import check

The fictional fixture is `output/pdf/Accord_Test_Meeting.pdf`. It is a product smoke test, not AMI data, a new benchmark, or evidence of deployment accuracy.

## Try it

1. Open the local Accord workspace.
2. Beneath the Meeting selector, choose **Upload your own meeting**.
3. Select the PDF. Check the editable text preview and remove the title, page number and footer if you want only speech turns.
4. Choose **Local rules** and click **Import & extract actions**. No external model call or charge is required.
5. Find the saved meeting in the **Your uploaded meetings** group below the examples.

## Expected result with current local rules

Three explicit self-commitments are drafted:

| Owner | Task | Deadline phrase to confirm manually |
|---|---|---|
| Alex | Send the revised onboarding checklist | by Friday |
| Priya | Review the checklist and share comments | by Monday |
| Mia | Update the help page text | before the next meeting |

Local rules retain deadline wording inside the task but leave the deadline field unstated. Use Edit to confirm it. Do not invent calendar dates: this fixture has no meeting date.

A fourth task, Noah checking the FAQ links before the next meeting, is requested by Sam and accepted by Noah. Current local rules miss this cross-speaker assignment. Add it manually with evidence from both turns. After removing non-transcript lines, these are T0007 and T0008; use their full generated IDs from the workspace when entering evidence.

The chatbot is only a suggestion and must not become an action. Previous checklist review is completed work and must not become a new task.

## Observed workflow

The actual PDF was uploaded through the in-app browser file picker, parsed, previewed, cleaned and imported. Three drafts appeared with the expected owners. Noah's missed task was added with both exact quotes and saved in the approved register. Outstanding candidates continued to block export. Reopening the imported meeting from its grouped selector preserves the saved review.

Chrome automated upload was blocked by the browser extension's local-file permission. No permissions were changed. This restriction does not prevent the user from selecting the file manually.

The optional PDF builder requires ReportLab in addition to the app dependencies. The checked-in PDF can be used without installing ReportLab.
