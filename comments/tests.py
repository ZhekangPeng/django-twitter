from testing.testcases import TestCase

class CommentModelTest(TestCase):

    def test_comment(self):
        user = self.create_user("zhekang")
        tweet = self.create_tweet(user)
        comment = self.create_comment(user, tweet.id)
        self.assertNotEqual(comment.__str__(), None)


