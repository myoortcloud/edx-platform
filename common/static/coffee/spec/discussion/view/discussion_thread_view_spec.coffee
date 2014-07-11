describe "DiscussionThreadView", ->
    beforeEach ->
        DiscussionSpecHelper.setUpGlobals()
        setFixtures(
            """
            <script type="text/template" id="thread-template">
                <article class="discussion-article">
                    <div class="forum-thread-main-wrapper">
                        <div class="thread-content-wrapper"></div>
                        <div class="post-extended-content">
                            <ol class="responses js-marked-answer-list"></ol>
                        </div>
                    </div>
                    <div class="post-extended-content">
                        <div class="response-count"></div>
                        <ol class="responses js-response-list"></ol>
                        <div class="response-pagination"></div>
                    </div>
                    <div class="post-tools">
                        <a href="javascript:void(0)" class="forum-thread-expand">Expand</a>
                        <a href="javascript:void(0)" class="forum-thread-collapse">Collapse</a>
                    </div>
                </article>
            </script>
            <script type="text/template" id="thread-show-template">
                <div class="discussion-post">
                    <div class="post-body"><%- body %></div>
                </div>
            </script>
            <script type="text/template" id="thread-response-template">
                <div class="response"></div>
            </script>
            <div class="thread-fixture"/>
            """
        )

        jasmine.Clock.useMock()
        @threadData = DiscussionViewSpecHelper.makeThreadWithProps({})
        @thread = new Thread(@threadData)
        spyOn($, "ajax")
        # Avoid unnecessary boilerplate
        spyOn(DiscussionThreadShowView.prototype, "convertMath")
        spyOn(DiscussionContentView.prototype, "makeWmdEditor")
        spyOn(ThreadResponseView.prototype, "renderShowView")

    renderWithContent = (view, content) ->
        DiscussionViewSpecHelper.setNextResponseContent(content)
        view.render()
        jasmine.Clock.tick(100)

    assertContentVisible = (view, selector, visible) ->
        content = view.$el.find(selector)
        expect(content.length).toBeGreaterThan(0)
        content.each (i, elem) ->
            expect($(elem).is(":visible")).toEqual(visible)

    assertExpandedContentVisible = (view, expanded) ->
        expect(view.$el.hasClass("expanded")).toEqual(expanded)
        assertContentVisible(view, ".post-extended-content", expanded)
        assertContentVisible(view, ".forum-thread-expand", not expanded)
        assertContentVisible(view, ".forum-thread-collapse", expanded)

    assertResponseCountAndPaginationCorrect = (view, countText, displayCountText, buttonText) ->
        expect(view.$el.find(".response-count").text()).toEqual(countText)
        if displayCountText
            expect(view.$el.find(".response-display-count").text()).toEqual(displayCountText)
        else
            expect(view.$el.find(".response-display-count").length).toEqual(0)
        if buttonText
            expect(view.$el.find(".load-response-button").text()).toEqual(buttonText)
        else
            expect(view.$el.find(".load-response-button").length).toEqual(0)

    describe "tab mode", ->
        beforeEach ->
            @view = new DiscussionThreadView({ model: @thread, el: $(".thread-fixture"), mode: "tab"})

        describe "response count and pagination", ->
            it "correctly render for a thread with no responses", ->
                renderWithContent(@view, {resp_total: 0, children: []})
                assertResponseCountAndPaginationCorrect(@view, "0 responses", null, null)

            it "correctly render for a thread with one response", ->
                renderWithContent(@view, {resp_total: 1, children: [{}]})
                assertResponseCountAndPaginationCorrect(@view, "1 response", "Showing all responses", null)

            it "correctly render for a thread with one additional page", ->
                renderWithContent(@view, {resp_total: 2, children: [{}]})
                assertResponseCountAndPaginationCorrect(@view, "2 responses", "Showing first response", "Load all responses")

            it "correctly render for a thread with multiple additional pages", ->
                renderWithContent(@view, {resp_total: 111, children: [{}, {}]})
                assertResponseCountAndPaginationCorrect(@view, "111 responses", "Showing first 2 responses", "Load next 100 responses")

            describe "on clicking the load more button", ->
                beforeEach ->
                    renderWithContent(@view, {resp_total: 5, children: [{}]})
                    assertResponseCountAndPaginationCorrect(@view, "5 responses", "Showing first response", "Load all responses")

                it "correctly re-render when all threads have loaded", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 5, children: [{}, {}, {}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertResponseCountAndPaginationCorrect(@view, "5 responses", "Showing all responses", null)

                it "correctly re-render when one page remains", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 42, children: [{}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertResponseCountAndPaginationCorrect(@view, "42 responses", "Showing first 3 responses", "Load all responses")

                it "correctly re-render when multiple pages remain", ->
                    DiscussionViewSpecHelper.setNextResponseContent({resp_total: 111, children: [{}, {}]})
                    @view.$el.find(".load-response-button").click()
                    assertResponseCountAndPaginationCorrect(@view, "111 responses", "Showing first 3 responses", "Load next 100 responses")

    describe "inline mode", ->
        beforeEach ->
            @view = new DiscussionThreadView({ model: @thread, el: $(".thread-fixture"), mode: "inline"})

        describe "render", ->
            it "shows content that should be visible when collapsed", ->
                @view.render()
                assertExpandedContentVisible(@view, false)

            it "does not render any responses by default", ->
                @view.render()
                expect($.ajax).not.toHaveBeenCalled()
                expect(@view.$el.find(".responses li").length).toEqual(0)

        describe "expand/collapse", ->
            it "shows/hides appropriate content", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                @view.render()
                @view.expand()
                assertExpandedContentVisible(@view, true)
                @view.collapse()
                assertExpandedContentVisible(@view, false)

            it "switches between the abbreviated and full body", ->
                DiscussionViewSpecHelper.setNextResponseContent({resp_total: 0, children: []})
                longBody = new Array(100).join("test ")
                expectedAbbreviation = DiscussionUtil.abbreviateString(longBody, 140)
                @thread.set("body", longBody)

                @view.render()
                expect($(".post-body").text()).toEqual(expectedAbbreviation)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
                DiscussionThreadShowView.prototype.convertMath.reset()

                @view.expand()
                expect($(".post-body").text()).toEqual(longBody)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()
                DiscussionThreadShowView.prototype.convertMath.reset()

                @view.collapse()
                expect($(".post-body").text()).toEqual(expectedAbbreviation)
                expect(DiscussionThreadShowView.prototype.convertMath).toHaveBeenCalled()

    describe "for question threads", ->
        beforeEach ->
            @thread.set("thread_type", "question")
            @view = new DiscussionThreadView(
                {model: @thread, el: $(".thread-fixture"), mode: "tab"}
            )

        it "renders correctly with no marked answers and 1 response", ->
            renderWithContent(
                @view,
                {
                    endorsed_responses: [],
                    non_endorsed_responses: [{id: "1"}],
                    non_endorsed_resp_total: 1
                }
            )
            expect($(".js-marked-answer-list .response").length).toEqual(0)
            expect($(".js-response-list .response").length).toEqual(1)
            assertResponseCountAndPaginationCorrect(
                @view,
                "1 response",
                "Showing all responses",
                null
            )

        it "renders correctly with no marked answers and many responses", ->
            renderWithContent(
                @view,
                {
                    endorsed_responses: [],
                    non_endorsed_responses: [{id: "1"}, {id: "2"}, {id: "3"}],
                    non_endorsed_resp_total: 42
                }
            )
            expect($(".js-marked-answer-list .response").length).toEqual(0)
            expect($(".js-response-list .response").length).toEqual(3)
            assertResponseCountAndPaginationCorrect(
                @view,
                "42 responses",
                "Showing first 3 responses",
                "Load all responses"
            )

        it "renders correctly with marked answers and 1 other response", ->
            renderWithContent(
                @view,
                {
                    endorsed_responses: [{id: "1"}, {id: "2"}],
                    non_endorsed_responses: [{id: "3"}],
                    non_endorsed_resp_total: 1
                }
            )
            expect($(".js-marked-answer-list .response").length).toEqual(2)
            expect($(".js-response-list .response").length).toEqual(1)
            assertResponseCountAndPaginationCorrect(
                @view,
                "1 other response",
                "Showing all responses",
                null
            )

        it "renders correctly with marked answers and many other responses", ->
            renderWithContent(
                @view,
                {
                    endorsed_responses: [{id: "1"}, {id: "2"}],
                    non_endorsed_responses: [{id: "3"}, {id: "4"}, {id: "5"}],
                    non_endorsed_resp_total: 42
                }
            )
            expect($(".js-marked-answer-list .response").length).toEqual(2)
            expect($(".js-response-list .response").length).toEqual(3)
            assertResponseCountAndPaginationCorrect(
                @view,
                "42 other responses",
                "Showing first 3 responses",
                "Load all responses"
            )

        it "handles pagination correctly", ->
            renderWithContent(
                @view,
                {
                    endorsed_responses: [{id: "1"}, {id: "2"}],
                    non_endorsed_responses: [{id: "3"}, {id: "4"}, {id: "5"}],
                    non_endorsed_resp_total: 42
                }
            )
            DiscussionViewSpecHelper.setNextResponseContent({
                # Add an endorsed response; it should be rendered
                endorsed_responses: [{id: "1"}, {id: "2"}, {id: "6"}],
                non_endorsed_responses: [{id: "7"}, {id: "8"}, {id: "9"}],
                non_endorsed_resp_total: 41
            })
            @view.$el.find(".load-response-button").click()
            expect($(".js-marked-answer-list .response").length).toEqual(3)
            expect($(".js-response-list .response").length).toEqual(6)
            assertResponseCountAndPaginationCorrect(
                @view,
                "41 other responses",
                "Showing first 6 responses",
                "Load all responses"
            )
