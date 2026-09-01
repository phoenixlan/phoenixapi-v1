# The permission system

Phoenix API uses a RBAC-based system where 

## High-level chart

```
  erDiagram
      User ||--o{ "Position mapping" : has
      "Position mapping" }o--|| Position : "maps to"
      "Position mapping" }o--o| Event : "scoped to"

      Position ||--o{ Permission : has
      Permission }o--o| Event : "scoped to"

      Position }o--o| "Event brand" : "owned by"
      Position }o--o| Crew : "belongs to"
      Position }o--o| Team : "belongs to"

      Team }o--|| Crew : "part of"
      Crew }o--|| "Event brand" : "owned by"
      Event }o--o| "Event brand" : "run by"
```

The TL;DR is: Users don't have permissions. They are mapped to **positions**, which have permissions. This happens through a Position mapping, which describes that "The user X has the position Y". In most cases, it specifies the event for which the mapping counts.

Event brands are collections of events which happen independently. When determining what permissions are currently active, the system will figure out what events are current - one for each brand, and use them to look up corresponding mappings. PhoenixAPI does not aim to allow modifying events that have passed - the data is kept for prosterity and should not be modified. Therefore, a permission mapping goes from having authorization use to being simply a record of a prior involvement once the associated event has passed. The current event for a given brand is the closest upcoming event.

In practice, this means PhoenixAPI stores users involvement in flat organziational charts, one per event brand. The system derives permissions from currently active positions.
