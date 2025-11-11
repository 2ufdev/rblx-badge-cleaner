A Python utility to scrape and selectively delete badges from your Roblox profile, with support for exempting specific games or badges based on keywords. This tool helps clean up your inventory while preserving meaningful achievements.

**Original Script Credit**: This project is a fork and enhanced version of the original Roblox Badge Removal script by [dieperdev](https://github.com/dieperdev/roblox-badge-removal). All improvements (e.g., rate limiting, dry run, better exemptions) build upon their foundational work—thanks for the awesome starting point!

## Features
- **Pagination Support**: Fetches all badges across multiple pages (up to Roblox's API limits).
- **Exemption Rules**: Skip deletion for badges from specific games (by Universe ID) or containing exempt keywords (case-insensitive, in name or description).
- **Dry Run Mode**: Preview deletions without actually removing badges.
- **Rate Limit Handling**: Automatic retries with exponential backoff to avoid Roblox API throttling (429 errors).
- **Detailed Logging**: Shows queued deletions, exemptions, and summaries for transparency.
- **Error Resilience**: Handles API errors gracefully and reports failures.

## Prerequisites
- Python 3.8+ installed.
- `pip` for installing dependencies.
- A Roblox account with badges to remove (obviously!).

## Setup

### Getting Your Roblox Security Token
- Log into Roblox in your browser.
- Open Developer Tools (F12) > Application/Storage tab > Cookies > Find `.ROBLOSECURITY` under `roblox.com`.
- Copy the value (starts with `_`).  
  **Warning**: Treat this like a password—it's your session cookie. Never share it. This script only uses it for authenticated Roblox API calls. If compromised, log out and clear cookies.

### Environment Variables
Create a `.env` file in the root directory with the following:

```
ROBLOSECURITY=your_roblosecurity_cookie_here
USERID=your_roblox_user_id_here  # e.g., 123456789 (find via roblox.com/users/ID/profile)

# Optional: Comma-separated game Universe IDs to exempt (e.g., 1,17 for classics like Adopt Me)
GAMES_EXEMPT=

# Optional: Comma-separated keywords to exempt badges containing them (case-insensitive)
KEYWORDS_EXEMPT=welcome,achievement,beta

# Optional: Enable dry run (no actual deletions)
DRY_RUN=true
```

- **USERID**: Your numeric Roblox User ID (not username). Get it from your profile URL.
- Leave `GAMES_EXEMPT` or `KEYWORDS_EXEMPT` blank/empty for no exemptions—all badges will be candidates for deletion.
- Set `DRY_RUN=true` to test without deleting.

## Usage
Run the script from the command line:

```
python main.py
```

### What Happens?
1. **Scraping**: Fetches your badges in batches of 100 (sorted newest first).
2. **Filtering**: Applies exemptions and queues non-exempt badges.
3. **Preview (Dry Run)**: If enabled, lists what would be deleted without action.
4. **Deletion**: Attempts to delete queued badges one-by-one, with logging.
   - Success: "Deleted Badge ID #123... Total deleted: X. Y remain."
   - Rate Limit (429): Retries up to 5 times with increasing delays (1s → 2s → 4s → 8s → 16s).
   - Other Errors: Logs the status and skips.

### Example Output
```
Exempt games: []
Exempt keywords: ['welcome']
Dry run mode: False
Badge ID #123 queued for deletion (Achievement Unlocked... from game 456).
Badge ID #789 was exempt from badge removal (keyword: 'welcome' (Welcome Badge...)).

--- SUMMARY ---
Total scraped: ~700
Exempt by game: 0
Exempt by keyword: 50
Candidates for deletion: 650 (unhandled: 650)

Deleting badges...
Deleted Badge ID #123. Total deleted: 1. 649 remain.
Rate limited on Badge ID #456 (attempt 2/5). Waiting 2s...
```

## Rate Limiting & Best Practices
- Roblox enforces API limits (~100-200 requests/minute for deletions). The script includes a 0.2s base delay + exponential backoff.
- For large inventories (>500 badges), run in batches or with longer delays—edit `time.sleep(0.2)` if needed.
- If throttled heavily, pause and resume (script doesn't save progress; re-run skips already-deleted badges as they're gone from API).

## Troubleshooting
- **"All environment variables must be entered"**: Check `.env` for missing `ROBLOSECURITY` or `USERID`.
- **CSRF Token Errors**: Re-run; token refreshes automatically.
- **No Badges Found**: You have none, or API issue—verify User ID.
- **Empty Exempt Lists Show `['']`**: Ensure no trailing spaces in `.env` (e.g., `KEYWORDS_EXEMPT= ,` becomes `[' ', '']`—always trim).
- **Deletions Fail (403/401)**: Invalid token—regenerate `.ROBLOSECURITY`.
- **Script Crashes**: Check Python version or deps. Report issues with full traceback.

## Security & Disclaimer
- This script makes direct API calls to Roblox—your token never leaves your machine.
- Deleting badges is permanent; use dry run first!
- Roblox may change APIs; test on a alt account if paranoid.
- Not affiliated with Roblox Corp. Use at your own risk.

## Contributing
Fork, PR improvements (e.g., more exemptions, GUI). Issues welcome!

## License
MIT License—do whatever, just credit if sharing.
