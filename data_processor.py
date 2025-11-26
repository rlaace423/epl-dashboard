"""
데이터 전처리 및 유망주 점수 계산 모듈
"""
import pandas as pd
import numpy as np


class FootballDataProcessor:
    """축구 선수 데이터를 처리하고 유망주 점수를 계산하는 클래스"""
    
    # 능력치 카테고리별 컬럼 정의
    TECHNICAL_ATTRIBUTES = [
        'Corners', 'Crossing', 'Dribbling', 'Finishing', 'FirstTouch', 
        'Freekicks', 'Heading', 'LongShots', 'Marking', 'Passing', 
        'PenaltyTaking', 'Tackling', 'Technique'
    ]
    
    MENTAL_ATTRIBUTES = [
        'Aggression', 'Anticipation', 'Bravery', 'Composure', 'Concentration',
        'Vision', 'Decisions', 'Determination', 'Flair', 'Leadership',
        'OffTheBall', 'Positioning', 'Teamwork', 'Workrate'
    ]
    
    PHYSICAL_ATTRIBUTES = [
        'Acceleration', 'Agility', 'Balance', 'Jumping', 'NaturalFitness',
        'Pace', 'Stamina', 'Strength'
    ]
    
    # 포지션별 중요 능력치
    POSITION_ATTRIBUTES = {
        'Goalkeeper': ['AerialAbility', 'CommandOfArea', 'Handling', 'Kicking', 
                      'OneOnOnes', 'Reflexes', 'RushingOut', 'Throwing'],
        'Defender': ['Marking', 'Tackling', 'Heading', 'Positioning', 'Strength',
                    'Anticipation', 'Bravery', 'Concentration'],
        'Midfielder': ['Passing', 'Vision', 'Technique', 'FirstTouch', 'Stamina',
                      'Workrate', 'Decisions', 'Teamwork'],
        'Forward': ['Finishing', 'Dribbling', 'Pace', 'Acceleration', 'OffTheBall',
                   'Composure', 'FirstTouch', 'Technique']
    }
    
    def __init__(self, csv_path):
        """
        데이터 프로세서 초기화
        
        Args:
            csv_path: CSV 파일 경로
        """
        self.csv_path = csv_path
        self.df = None
        self.processed_df = None
        
    def load_data(self):
        """CSV 데이터 로드"""
        print("데이터를 로딩 중...")
        self.df = pd.read_csv(self.csv_path)
        print(f"총 {len(self.df)} 명의 선수 데이터를 로드했습니다.")
        return self.df
    
    def calculate_overall_rating(self):
        """종합 능력치 계산 (기술/정신/신체 능력치 평균)"""
        # 골키퍼가 아닌 선수들에 대한 능력치 계산
        self.df['Technical_Rating'] = self.df[self.TECHNICAL_ATTRIBUTES].mean(axis=1)
        self.df['Mental_Rating'] = self.df[self.MENTAL_ATTRIBUTES].mean(axis=1)
        self.df['Physical_Rating'] = self.df[self.PHYSICAL_ATTRIBUTES].mean(axis=1)
        
        # 종합 평점 (세 카테고리의 평균)
        self.df['Overall_Rating'] = (
            self.df['Technical_Rating'] * 0.4 +
            self.df['Mental_Rating'] * 0.35 +
            self.df['Physical_Rating'] * 0.25
        )
        
        return self.df
    
    def calculate_potential_score(self):
        """
        잠재력 점수 계산
        나이가 어릴수록, 현재 능력치가 높을수록 높은 점수
        """
        # 나이 가중치: 젊을수록 높은 가중치
        # 18-21세: 1.5배, 22-25세: 1.2배, 26-29세: 1.0배, 30세 이상: 0.5배
        age_weight = np.where(self.df['Age'] <= 21, 1.5,
                     np.where(self.df['Age'] <= 25, 1.2,
                     np.where(self.df['Age'] <= 29, 1.0, 0.5)))
        
        self.df['Age_Weight'] = age_weight
        self.df['Potential_Score'] = self.df['Overall_Rating'] * age_weight
        
        return self.df
    
    def identify_primary_position(self):
        """선수의 주 포지션 식별"""
        position_cols = [
            'Goalkeeper', 'Sweeper', 'Striker', 'AttackingMidCentral',
            'AttackingMidLeft', 'AttackingMidRight', 'DefenderCentral',
            'DefenderLeft', 'DefenderRight', 'DefensiveMidfielder',
            'MidfielderCentral', 'MidfielderLeft', 'MidfielderRight',
            'WingBackLeft', 'WingBackRight'
        ]
        
        # 각 선수의 최고 포지션 숙련도 찾기
        position_values = self.df[position_cols]
        self.df['Primary_Position'] = position_values.idxmax(axis=1)
        self.df['Position_Rating'] = position_values.max(axis=1)
        
        # 포지션 카테고리 매핑
        def categorize_position(pos):
            if pos == 'Goalkeeper':
                return 'Goalkeeper'
            elif 'Defender' in pos or 'Sweeper' in pos or 'WingBack' in pos:
                return 'Defender'
            elif 'Midfielder' in pos or 'Attacking' in pos or 'Defensive' in pos:
                return 'Midfielder'
            elif 'Striker' in pos:
                return 'Forward'
            else:
                return 'Midfielder'
        
        self.df['Position_Category'] = self.df['Primary_Position'].apply(categorize_position)
        
        return self.df
    
    def calculate_position_specialized_score(self):
        """포지션별 특화 점수 계산"""
        def get_position_score(row):
            category = row['Position_Category']
            if category in self.POSITION_ATTRIBUTES:
                attrs = self.POSITION_ATTRIBUTES[category]
                available_attrs = [attr for attr in attrs if attr in self.df.columns]
                if available_attrs:
                    return row[available_attrs].mean()
            return row['Overall_Rating']
        
        self.df['Position_Specialized_Score'] = self.df.apply(get_position_score, axis=1)
        
        return self.df
    
    def calculate_talent_score(self):
        """
        최종 유망주 점수 계산
        = 종합 능력치 (40%) + 잠재력 점수 (40%) + 포지션 특화 점수 (20%)
        """
        self.df['Talent_Score'] = (
            self.df['Overall_Rating'] * 0.4 +
            self.df['Potential_Score'] * 0.4 +
            self.df['Position_Specialized_Score'] * 0.2
        )
        
        # 정규화 (0-100 범위)
        min_score = self.df['Talent_Score'].min()
        max_score = self.df['Talent_Score'].max()
        self.df['Talent_Score_Normalized'] = ((self.df['Talent_Score'] - min_score) / 
                                               (max_score - min_score) * 100)
        
        return self.df
    
    def process_all(self):
        """전체 데이터 처리 파이프라인 실행"""
        print("데이터 처리를 시작합니다...")
        
        # 데이터 로드
        self.load_data()
        
        # 각 단계별 처리
        print("종합 능력치를 계산 중...")
        self.calculate_overall_rating()
        
        print("잠재력 점수를 계산 중...")
        self.calculate_potential_score()
        
        print("주 포지션을 식별 중...")
        self.identify_primary_position()
        
        print("포지션별 특화 점수를 계산 중...")
        self.calculate_position_specialized_score()
        
        print("최종 유망주 점수를 계산 중...")
        self.calculate_talent_score()
        
        self.processed_df = self.df.copy()
        print("데이터 처리가 완료되었습니다!")
        
        return self.processed_df
    
    def get_top_talents(self, n=50, age_range=None, position=None, min_rating=None):
        """
        상위 유망주 선수 추출
        
        Args:
            n: 반환할 선수 수
            age_range: (min_age, max_age) 튜플
            position: 포지션 카테고리 필터
            min_rating: 최소 능력치
            
        Returns:
            필터링된 상위 유망주 DataFrame
        """
        df_filtered = self.processed_df.copy()
        
        # 필터 적용
        if age_range:
            df_filtered = df_filtered[
                (df_filtered['Age'] >= age_range[0]) & 
                (df_filtered['Age'] <= age_range[1])
            ]
        
        if position and position != 'All':
            df_filtered = df_filtered[df_filtered['Position_Category'] == position]
        
        if min_rating:
            df_filtered = df_filtered[df_filtered['Overall_Rating'] >= min_rating]
        
        # 유망주 점수로 정렬하여 상위 n명 반환
        return df_filtered.nlargest(n, 'Talent_Score_Normalized')
    
    def get_player_details(self, player_uid):
        """특정 선수의 상세 정보 반환"""
        return self.processed_df[self.processed_df['UID'] == player_uid].iloc[0]


def load_and_process_data(csv_path):
    """
    데이터 로드 및 처리 헬퍼 함수
    
    Args:
        csv_path: CSV 파일 경로
        
    Returns:
        처리된 DataFrame
    """
    processor = FootballDataProcessor(csv_path)
    return processor.process_all()

