# Brave Goggle Starter

This workspace is a small starter kit for creating your own Brave Search Goggle.

Brave Goggles are plain text files that tell Brave Search how to rerank results. You can boost useful sites, downrank noisy ones, or discard sites entirely.

## Files

- `goggles/my.goggle` - your editable Goggle.
- `data/allowed-sites.csv` - the normalized domains used in the allowlist.
- `examples/research-and-docs.goggle` - a small working example you can copy from.
- `docs/rule-design.md` - a worksheet for deciding what to boost, downrank, or remove.
- `scripts/build_allowlist_goggle.py` - regenerate the allowlist from a CSV export.
- `scripts/validate_goggle.py` - local syntax and limits checks before you submit.

## Edit Your Goggle

The current `goggles/my.goggle` is an allowlist generated from the first tab of this Google Sheet:

<https://docs.google.com/spreadsheets/d/1fxu7W_IuWByV1wOSBg0emny4M-1RCS1W1mun_wTcIQY/edit?usp=sharing>

It uses a generic `$discard` rule plus one `$boost,site=...` rule for each allowed domain. That means Brave should only keep results matching the listed websites.

To regenerate from a fresh CSV export of the first tab:

```bash
python3 scripts/build_allowlist_goggle.py /path/to/export.csv
```

The generated domain audit is saved to `data/allowed-sites.csv`.

For a hand-written Goggle, open `goggles/my.goggle` and change the metadata first:

```goggle
! name: My Starter Goggle
! description: Personal Brave Search ranking rules.
! public: false
! author: Me
```

Then add rules under the metadata. Common rule shapes:

```goggle
$boost=5,site=developer.mozilla.org
$downrank=2,site=example-content-farm.com
$discard,site=pinterest.com
/blog/$boost=3,site=example.com
|https://example.org^$boost=4
```

Notes:

- A line beginning with `!` is a comment, except metadata lines such as `! name:`.
- If a rule has no explicit action, Brave treats it as a boost.
- Boost and downrank strengths can go up to `10`.
- A generic `$discard` rule means "exclude everything that is not matched by another rule"; use it only when you want a narrow allowlist.

## Validate

Run:

```bash
python3 scripts/validate_goggle.py goggles/my.goggle
```

This checks the required metadata, common option mistakes, and Brave's published limits.

## Submit To Brave

When the file is ready:

1. Host the `.goggle` file on GitHub, GitLab, or a GitHub gist.
2. Copy the raw/plain-text file URL, not the pretty repository page URL.
3. Submit the hosted URL at <https://search.brave.com/goggles/create>.
4. After each update, submit the same URL again so Brave refetches and caches the new version.

For sharing, Brave supports this URL shape after the Goggle has been submitted:

```text
https://search.brave.com/goggles?goggles_id={YOUR_URL_ENCODED_GOGGLE_URL}
```
