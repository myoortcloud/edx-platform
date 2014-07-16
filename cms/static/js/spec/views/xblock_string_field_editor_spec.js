define(["jquery", "js/spec_helpers/create_sinon", "js/spec_helpers/view_helpers", "js/spec_helpers/edit_helpers", "js/models/xblock_info", "js/views/xblock_string_field_editor"],
       function ($, create_sinon, view_helpers, edit_helpers, XBlockInfo, XBlockStringFieldEditor) {
           describe("XBlockStringFieldEditorView", function () {
               var initialDisplayName, updatedDisplayName, getXBlockInfo, getFieldEditorView;

               initialDisplayName = "Default Display Name";
               updatedDisplayName = "Updated Display Name";

               getXBlockInfo = function (displayName) {
                   return new XBlockInfo(
                       { display_name: displayName },
                       { parse: true }
                   );
               };

               getFieldEditorView = function (xblockInfo) {
                   if (xblockInfo === undefined) {
                       xblockInfo = getXBlockInfo(initialDisplayName);
                   }
                   return new XBlockStringFieldEditor({
                       model: xblockInfo,
                       el: $('.wrapper-xblock-field')
                   });
               };

               beforeEach(function () {
                   view_helpers.installTemplate('xblock-string-field-editor');
                   appendSetFixtures(
                           '<div class="wrapper-xblock-field incontext-editor is-editable"' +
                           'data-field="display_name" data-field-display-name="Display Name">' +
                           '<h1 class="page-header-title xblock-field-value incontext-editor-value"><span class="title-value">' + initialDisplayName + '</span></h1>' +
                           '</div>'
                   );
               });

               describe('Editing', function () {
                   var expectEditCanceled = function (test, fieldEditorView, options) {
                       var requests, initialRequests, displayNameInput;
                       requests = create_sinon.requests(test);
                       initialRequests = requests.length;
                       displayNameInput = edit_helpers.inlineEdit(fieldEditorView.$el, options.newTitle);
                       if (options.pressEscape) {
                           displayNameInput.simulate("keydown", { keyCode: $.simulate.keyCode.ESCAPE });
                           displayNameInput.simulate("keyup", { keyCode: $.simulate.keyCode.ESCAPE });
                       } else {
                           displayNameInput.change();
                       }
                       // No requests should be made when the edit is cancelled client-side
                       expect(initialRequests).toBe(requests.length);
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, initialDisplayName);
                       expect(fieldEditorView.model.get('display_name')).toBe(initialDisplayName);
                   };

                   it('can inline edit the display name', function () {
                       var requests, fieldEditorView, displayNameInput;
                       requests = create_sinon.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       displayNameInput = edit_helpers.inlineEdit(fieldEditorView.$el, updatedDisplayName);
                       displayNameInput.change();
                       // This is the response for the change operation.
                       create_sinon.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       create_sinon.respondWithJson(requests, {display_name:  updatedDisplayName});
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, updatedDisplayName);
                       expect(fieldEditorView.model.get('display_name')).toBe(updatedDisplayName);
                   });

                   it('does not change the title when a display name update fails', function () {
                       var requests, fieldEditorView, initialRequests, displayNameInput;
                       requests = create_sinon.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       displayNameInput = edit_helpers.inlineEdit(fieldEditorView.$el, updatedDisplayName);
                       initialRequests = requests.length;
                       displayNameInput.change();
                       create_sinon.respondWithError(requests);
                       // No fetch operation should occur.
                       expect(initialRequests + 1).toBe(requests.length);
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, initialDisplayName, updatedDisplayName);
                       expect(fieldEditorView.model.get('display_name')).toBe(initialDisplayName);
                   });

                   it('trims whitespace from the display name', function () {
                       var requests, fieldEditorView, displayNameInput;
                       requests = create_sinon.requests(this);
                       fieldEditorView = getFieldEditorView().render();
                       displayNameInput = edit_helpers.inlineEdit(fieldEditorView.$el, updatedDisplayName + ' ');
                       displayNameInput.change();
                       // This is the response for the change operation.
                       create_sinon.respondWithJson(requests, { });
                       // This is the response for the subsequent fetch operation.
                       create_sinon.respondWithJson(requests, {display_name:  updatedDisplayName});
                       edit_helpers.verifyInlineEditChange(fieldEditorView.$el, updatedDisplayName);
                       expect(fieldEditorView.model.get('display_name')).toBe(updatedDisplayName);
                   });

                   it('does not change the title when input is the empty string', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: ''});
                   });

                   it('does not change the title when input is whitespace-only', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: ' '});
                   });

                   it('can cancel an inline edit', function () {
                       var fieldEditorView = getFieldEditorView().render();
                       expectEditCanceled(this, fieldEditorView, {newTitle: updatedDisplayName, pressEscape: true});
                   });
               });

               describe('Rendering', function () {
                   var expectInputMatchesModelDisplayName = function (displayName) {
                       var fieldEditorView = getFieldEditorView(getXBlockInfo(displayName)).render();
                       expect(fieldEditorView.$('.xblock-field-input').val()).toBe(displayName);
                   };

                   it('renders single quotes in input field', function () {
                       expectInputMatchesModelDisplayName('Updated \'Display Name\'');
                   });

                   it('renders double quotes in input field', function () {
                       expectInputMatchesModelDisplayName('Updated "Display Name"');
                   });

                   it('renders open angle bracket in input field', function () {
                       expectInputMatchesModelDisplayName(updatedDisplayName + '<');
                   });

                   it('renders close angle bracket in input field', function () {
                       expectInputMatchesModelDisplayName('>' + updatedDisplayName);
                   });
               });
           });
       });
