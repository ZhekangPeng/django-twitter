from testing.testcases import TestCase


class CommentModelTest(TestCase):

    def setUp(self):
        self.clear_cache()
        self.zhekang = self.create_user("zhekang")
        self.xiaohe = self.create_user('xiaohe')
        self.tweet = self.create_tweet(self.zhekang)
        self.comment = self.create_comment(self.zhekang, self.tweet.id)

    def test_comment(self):
        self.assertNotEqual(self.comment.__str__(), None)

    def test_like_set(self):
        # First like from zhekang
        self.create_like(user=self.zhekang, target=self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        # More like from the same person does not count
        self.create_like(user=self.zhekang, target=self.comment)
        self.assertEqual(self.comment.like_set.count(), 1)

        # Second like from xiaohe
        self.create_like(user=self.xiaohe, target=self.comment)
        self.assertEqual(self.comment.like_set.count(), 2)


