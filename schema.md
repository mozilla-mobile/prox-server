# Client<->Server Schema

## Place

```
Place: {
    version: #,
    id: "<yelp-id>",

    name: "",
    description: {
        provider: "wikipedia",
        text: ""
    },
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
