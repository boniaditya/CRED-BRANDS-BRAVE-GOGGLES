# Rule Design Worksheet

Use this before adding lots of rules. A good Goggle usually starts with a clear search habit, not a giant blocklist.

## Purpose

Write one sentence:

```text
I want Brave Search to prefer ...
```

Examples:

- Official docs and primary sources before tutorials.
- Independent blogs before SEO-heavy sites.
- Local Indian sources before global aggregators.
- Results about a specific programming language, community, or hobby.

## Domains To Boost

Add domains that are usually useful and trustworthy for this purpose.

```goggle
$boost=5,site=example.com
$boost=4,site=docs.example.org
```

## Domains To Downrank

Use downrank for sites that are sometimes useful but too often dominate the results.

```goggle
$downrank=2,site=example.com
```

## Domains To Discard

Use discard for sites you truly do not want to see.

```goggle
$discard,site=example.com
```

## Test Queries

Pick 5 to 10 searches you run often. After submitting the Goggle, test those queries and write down what got better or worse.

```text
query:
expected better result:
actual result:
change to make:
```

## Iteration Rules

- Add 5 to 20 rules at a time.
- Prefer `downrank` before `discard` unless the site is never useful.
- Keep `! public: false` until the results feel stable.
- Resubmit the hosted URL after each update so Brave refetches it.

