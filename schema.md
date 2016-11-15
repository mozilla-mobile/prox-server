# Client<->Server Schema

## Place

```
Place: {
    version: #,
    id: "<yelp-id>",

    name: "",
    description: [{
        provider: "wikipedia",
        text: ""
    },
    {
        provider: "yelp",
        text: ""
    }],
    url: "",
    phone: "", // consistent format

    address: [""],
    coordinates: {
        lat: #,
        lng: #
    },
    categories: [{
        id: "",
        text: ""
    }],

    # Ratings providers
    providers: {
        yelp: {
            rating: #, // normalized 0-5 w/ half values
            totalReviewCount: #,
            url: ""
        },
        tripAdvisor: {
            // ...
        } // ...
    },

    images: [{
        src: "", // url to image
        provider: "", // name to attribute on client
        providerURL: "" // e.g. click target for image
    }],

    hours: {
        monday: [
            ["6:30", "18:00"]
        ],
        tuesday: [
            ["20:00", "4:00"]
        ], // ...
    }
}
```

## Event

```
Event: {
    coordinates: {
        lat: #,
        lng: #
    },
    description: "", # Used for badging
    notification: "",
    localStartTime: "", # RFC 3339, e.g., "2016-11-10T18:00:00-10:00",
    localEndTime: "", # RFC 3339
    id: "<yelp-id>", # Best effort Yelp id
    url: "" # Optional: url to open when clicking on more information
}
```
