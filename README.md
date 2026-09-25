# FoodPrep Client Catalyzer V1.0

A private tool for Nati Press. After signing in, Nati enters a target’s name, title and company, chooses the service status and contact focus, and generates an outreach email to copy into Outlook.

Repo: https://github.com/jpress123/fpsales (separate from the personal site repo)

Live at: https://www.josephpress.com/fpsales/

GitHub serves every Pages repo under the account’s custom domain, so this address uses josephpress.com. The files live only in this repo and do not touch the personal site. To move it to its own domain later, add a CNAME file here and point that domain’s DNS to GitHub.

## Folder layout

```
fpsales/
├── index.html          # sign-in screen + email generator (reads data.enc.json)
├── data.enc.json       # the templates, encrypted. The only template file published.
├── build.py            # rebuilds data.enc.json from private/ (Python standard library only)
├── assets/logo.png     # FoodPrep logo, shown after sign-in
├── .gitignore          # keeps private/ off GitHub
├── _config.yml         # hides README.md and build.py from the public site
├── README.md
└── private/            # NEVER published (listed in .gitignore)
    ├── credentials.json            # Nati’s user name and password
    ├── FP_Sales_Email_samples.docx # original samples
    └── templates/
        ├── _signature.md           # signature added to every email
        ├── none.md                 # status: No knife service, fallback for Unknown role
        ├── none-procurement.md
        ├── none-purchasing.md
        ├── none-culinary.md
        ├── none-executive.md
        ├── cozzini-procurement.md
        ├── cozzini-purchasing.md
        ├── cozzini-culinary.md
        ├── cozzini-executive.md
        ├── cozzini-unknown.md      # Uses Cozzini, role unknown
        └── unknown.md              # status: Unknown (all focuses)
```

## Editing templates

1. Edit any file in `private/templates/` in a text editor.
2. In Terminal, from this folder, run: `python3 build.py`
3. In GitHub Desktop, commit and push `data.enc.json`.

Each template starts with a header:

```
---
profile: Knife Service Culinary Focus
status: cozzini          # none | cozzini | unknown
focus: culinary          # procurement | purchasing | culinary | executive | unknown | all
subject: Better knives for {{company_s}} kitchen teams
---
```

The site looks for `status-focus` first (e.g. `cozzini-culinary`), then falls back to the `focus: all` template for that status. To add a focus-specific version, e.g. a culinary email for “No knife service,” create `none-culinary.md` with `status: none` and `focus: culinary`.

### Placeholders

| Placeholder | Becomes |
|---|---|
| `{{greeting_name}}` | First name, or “Chef First” when focus is Culinary |
| `{{first_name}}` | First name |
| `{{name}}` | Full name as typed |
| `{{title}}` | Title as typed |
| `{{company}}` | Company as typed |
| `{{company_s}}` | Company possessive: Darden’s, Landry’s, Brinks’ |

## Using the site

- Sign-in ignores capitalization of the user name (Nati1 or nati1). The password is exact.
- Role is suggested from the title. General Manager counts as Executive.
- **Open in Outlook** opens a new message in the computer’s default mail app with subject and body filled in. Add the recipient’s email first to fill the To line. Set Outlook as the default mail app for this to open Outlook.
- If Nati edits the details after generating, the page flags the draft as out of date.

## Changing the password

Edit `private/credentials.json`, run `python3 build.py`, commit and push. The old password stops working once the push is live.

## Security notes

- Templates are encrypted (PBKDF2 + HMAC-SHA256, encrypt-then-MAC). Without the user name and password, `data.enc.json` is unreadable.
- `index.html` and the logo are public files. They reveal the layout and the status and focus options, not the email text.
- `private/` must stay out of git. Before each commit, check that GitHub Desktop lists no files under `private/`.
- Role is suggested from keywords in the title (chef, procurement, purchasing, VP, and so on) and defaults to Unknown. Nati can override it. In the template headers, the role is stored as `focus`.

## Rules

- Agents edit files on disk only and never run git. Joseph commits and pushes in GitHub Desktop.
