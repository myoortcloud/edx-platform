# -*- coding: utf-8 -*-

"""
Acceptance tests for CMS Video Editor.
"""

from .test_studio_video_module import CMSVideoBaseTest


class VideoEditorTest(CMSVideoBaseTest):
    """
    CMS Video Editor Test Class
    """

    def setUp(self):
        super(VideoEditorTest, self).setUp()

    def _create_video_component(self, subtitles=False):
        """
        Create a video component and navigate to unit page

        Arguments:
            subtitles (bool): Upload subtitles or not

        """
        if subtitles:
            self.assets.append('subs_OEoXaMPEzfM.srt.sjson')

        self.navigate_to_course_unit()

    def test_default_settings(self):
        """
        Scenario: User can view Video metadata
        Given I have created a Video component
        And I edit the component
        Then I see the correct video settings and default values
        """
        self._create_video_component()

        self.edit_component()

        self.assertTrue(self.video.verify_settings())

    def test_modify_video_display_name(self):
        """
        Scenario: User can modify Video display name
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        Then I can modify video display name
        And my video display name change is persisted on save
        """
        self._create_video_component()

        self.edit_component()

        self.open_advanced_tab()

        self.video.set_field_value('Component Display Name', 'Transformers')

        self.save_unit_settings()

        self.edit_component()

        self.open_advanced_tab()

        self.assertTrue(self.video.verify_field_value('Component Display Name', 'Transformers'))

    def test_hidden_captions(self):
        """
        Scenario: Captions are hidden when "transcript display" is false
        Given I have created a Video component with subtitles
        And I have set "transcript display" to False
        Then when I view the video it does not show the captions
        """
        self._create_video_component(subtitles=True)

        # Prevent cookies from overriding course settings
        self.browser.delete_cookie('hide_captions')

        self.edit_component()

        self.open_advanced_tab()

        self.video.set_field_value('Show Transcript', 'False', 'select')

        self.save_unit_settings()

        self.assertFalse(self.video.captions_visible())

    def test_shown_captions(self):
        """
        Scenario: Captions are shown when "transcript display" is true
        Given I have created a Video component with subtitles
        And I have set "transcript display" to True
        Then when I view the video it does show the captions
        """
        self._create_video_component(subtitles=True)

        # Prevent cookies from overriding course settings
        self.browser.delete_cookie('hide_captions')

        self.edit_component()

        self.open_advanced_tab()

        self.video.set_field_value('Show Transcript', 'True', 'select')

        self.save_unit_settings()

        self.assertTrue(self.video.captions_visible())

    def test_translations_uploading(self):
        """
        Scenario: Translations uploading works correctly
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "chinese_transcripts.srt" for "zh" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And I edit the component
        And I open tab "Advanced"
        And I see translations for "zh"
        And I upload transcript file "uk_transcripts.srt" for "uk" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "好 各位同学" text in the captions
        And video language menu has "uk, zh" translations
        """
        self._create_video_component()

        self.edit_component()

        self.open_advanced_tab()

        self.video.upload_translation('chinese_transcripts.srt', 'zh')

        self.save_unit_settings()

        self.assertTrue(self.video.captions_visible())

        unicode_text = "好 各位同学".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text())

        self.edit_component()

        self.open_advanced_tab()

        self.assertEqual(self.video.translations(), ['zh'])

        self.video.upload_translation('uk_transcripts.srt', 'uk')

        self.save_unit_settings()

        self.assertTrue(self.video.captions_visible())

        self.assertIn(unicode_text, self.video.captions_text())

        self.assertEqual(self.video.caption_languages().keys(), ['zh', 'uk'])

    def test_upload_large_transcript(self):
        """
        Scenario: User can upload transcript file with > 1mb size
        Given I have created a Video component
        And I edit the component
        And I open tab "Advanced"
        And I upload transcript file "1mb_transcripts.srt" for "uk" language code
        And I save changes
        Then when I view the video it does show the captions
        And I see "Привіт, edX вітає вас." text in the captions
        """
        self._create_video_component()

        self.edit_component()

        self.open_advanced_tab()

        self.video.upload_translation('1mb_transcripts.srt', 'uk')

        self.save_unit_settings()

        self.assertTrue(self.video.captions_visible())

        unicode_text = "Привіт, edX вітає вас.".decode('utf-8')
        self.assertIn(unicode_text, self.video.captions_text())
