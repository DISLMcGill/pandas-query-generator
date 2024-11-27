export const EXAMPLE_SCHEMAS = {
  sports: {
    entities: {
      team: {
        properties: {
          T_TEAMKEY: { type: 'string', starting_character: ['t'] },
          T_GROUP: {
            type: 'enum',
            values: ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'],
          },
          T_PLAYERCOUNT: { type: 'int', min: 18, max: 26 },
        },
        primary_key: 'T_TEAMKEY',
      },
      association: {
        properties: {
          A_ASSOCKEY: { type: 'string', starting_character: ['f'] },
          A_TEAMKEY: { type: 'string', starting_character: ['t'] },
          A_FOUNDEDYEAR: { type: 'int', min: 1900, max: 2000 },
          A_PRESIDENT: { type: 'string', starting_character: ['p'] },
        },
        primary_key: 'A_ASSOCKEY',
        foreign_keys: {
          A_TEAMKEY: ['T_TEAMKEY', 'team'],
        },
      },
      coach: {
        properties: {
          C_COACHKEY: { type: 'int', min: 1, max: 100 },
          C_ROLE: {
            type: 'enum',
            values: [
              'head coach',
              'assistant coach',
              'goalkeeper coach',
              'fitness coach',
            ],
          },
          C_TEAMKEY: { type: 'string', starting_character: ['t'] },
          C_NAME: { type: 'string', starting_character: ['c'] },
          C_EXPYEARS: { type: 'int', min: 1, max: 40 },
        },
        primary_key: ['C_COACHKEY', 'C_TEAMKEY'],
        foreign_keys: {
          C_TEAMKEY: ['T_TEAMKEY', 'team'],
        },
      },
      stadium: {
        properties: {
          S_STADIUMKEY: { type: 'int', min: 1, max: 12 },
          S_NAME: { type: 'string', starting_character: ['s'] },
          S_CITY: { type: 'string', starting_character: ['d', 'a', 'l', 'r'] },
          S_LOCATION: {
            type: 'string',
            starting_character: ['n', 's', 'e', 'w', 'c'],
          },
          S_CAPACITY: { type: 'int', min: 40000, max: 90000 },
          S_YEARBUILT: { type: 'int', min: 1950, max: 2022 },
        },
        primary_key: 'S_STADIUMKEY',
      },
      match: {
        properties: {
          M_MATCHKEY: { type: 'int', min: 1, max: 64 },
          M_TEAM1KEY: { type: 'string', starting_character: ['t'] },
          M_TEAM2KEY: { type: 'string', starting_character: ['t'] },
          M_STADIUMKEY: { type: 'int', min: 1, max: 12 },
          M_DATE: { type: 'date', min: '2022-11-20', max: '2022-12-18' },
          M_TIME: { type: 'string', starting_character: ['1', '2'] },
          M_DURATION: { type: 'int', min: 90, max: 150 },
          M_ROUND: {
            type: 'enum',
            values: [
              'group stage',
              'round of 16',
              'quarter-final',
              'semi-final',
              'final',
            ],
          },
          M_SCORE1: { type: 'int', min: 0, max: 7 },
          M_SCORE2: { type: 'int', min: 0, max: 7 },
          M_ATTENDANCE: { type: 'int', min: 30000, max: 90000 },
        },
        primary_key: 'M_MATCHKEY',
        foreign_keys: {
          M_TEAM1KEY: ['T_TEAMKEY', 'team'],
          M_TEAM2KEY: ['T_TEAMKEY', 'team'],
          M_STADIUMKEY: ['S_STADIUMKEY', 'stadium'],
        },
      },
    },
  },
  tpch: {
    entities: {
      customer: {
        properties: {
          C_CUSTKEY: { type: 'int', min: 1, max: 100 },
          C_NAME: { type: 'string', starting_character: ['C'] },
          C_ADDRESS: {
            type: 'string',
            starting_character: [
              'I',
              'H',
              'X',
              's',
              '9',
              'n',
              'z',
              'K',
              'T',
              'u',
              'Q',
              'O',
              '7',
            ],
          },
          C_NATIONKEY: { type: 'int', min: 0, max: 23 },
          C_PHONE: {
            type: 'string',
            starting_character: [
              '1',
              '2',
              '3',
              '25-',
              '13-',
              '27-',
              '18-',
              '22-',
            ],
          },
          C_ACCTBAL: { type: 'float', min: -917.25, max: 9983.38 },
          MKTSEGMENT: {
            type: 'enum',
            values: [
              'BUILDING',
              'AUTOMOBILE',
              'MACHINERY',
              'HOUSEHOLD',
              'FURNITURE',
            ],
          },
          C_COMMENT: {
            type: 'string',
            starting_character: ['i', 's', 'l', 'r', 'c', 't', 'e'],
          },
        },
        primary_key: 'C_CUSTKEY',
        foreign_keys: {
          C_NATIONKEY: ['N_NATIONKEY', 'nation'],
        },
      },
      lineitem: {
        properties: {
          L_ORDERKEY: { type: 'int', min: 1, max: 194 },
          L_PARTKEY: { type: 'int', min: 450, max: 198344 },
          L_SUPPKEY: { type: 'int', min: 22, max: 9983 },
          LINENUMBER: { type: 'int', min: 1, max: 7 },
          QUANTITY: { type: 'int', min: 1, max: 50 },
          EXTENDEDPRICE: { type: 'float', min: 1606.52, max: 88089.08 },
          DISCOUNT: { type: 'float', min: 0.0, max: 0.1 },
          TAX: { type: 'float', min: 0.0, max: 0.08 },
          RETURNFLAG: { type: 'enum', values: ['N', 'R', 'A'] },
          LINESTATUS: { type: 'enum', values: ['O', 'F'] },
          SHIPDATE: { type: 'date', min: '1992-04-27', max: '1998-10-30' },
          COMMITDATE: { type: 'date', min: '1992-05-15', max: '1998-10-16' },
          RECEIPTDATE: { type: 'date', min: '1992-05-02', max: '1998-11-06' },
          SHIPINSTRUCT: {
            type: 'enum',
            values: [
              'DELIVER IN PERSON',
              'TAKE BACK RETURN',
              'NONE',
              'COLLECT COD',
            ],
          },
          SHIPMODE: {
            type: 'enum',
            values: ['TRUCK', 'MAIL', 'REG AIR', 'AIR', 'FOB', 'RAIL', 'SHIP'],
          },
        },
        primary_key: ['L_ORDERKEY', 'L_PARTKEY', 'L_SUPPKEY'],
        foreign_keys: {
          L_ORDERKEY: ['O_ORDERKEY', 'orders'],
          L_PARTKEY: ['PS_PARTKEY', 'partsupp'],
          L_SUPPKEY: ['PS_SUPPKEY', 'partsupp'],
        },
      },
      nation: {
        properties: {
          N_NATIONKEY: { type: 'int', min: 0, max: 24 },
          N_NAME: {
            type: 'string',
            starting_character: [
              'I',
              'A',
              'C',
              'E',
              'J',
              'M',
              'R',
              'U',
              'B',
              'F',
              'G',
              'K',
              'P',
              'S',
              'V',
            ],
          },
          N_REGIONKEY: { type: 'int', min: 0, max: 4 },
          N_COMMENT: {
            type: 'string',
            starting_character: [' ', 'y', 'e', 'r', 's', 'a', 'v', 'l'],
          },
        },
        primary_key: 'N_NATIONKEY',
        foreign_keys: {
          N_REGIONKEY: ['R_REGIONKEY', 'region'],
        },
      },
      orders: {
        properties: {
          O_ORDERKEY: { type: 'int', min: 1, max: 800 },
          O_CUSTKEY: { type: 'int', min: 302, max: 149641 },
          ORDERSTATUS: { type: 'enum', values: ['O', 'F', 'P'] },
          TOTALPRICE: { type: 'float', min: 1156.67, max: 355180.76 },
          ORDERDATE: { type: 'date', min: '1992-01-13', max: '1998-07-21' },
          ORDERPRIORITY: {
            type: 'enum',
            values: [
              '1-URGENT',
              '2-HIGH',
              '3-MEDIUM',
              '4-NOT SPECIFIED',
              '5-LOW',
            ],
          },
          CLERK: { type: 'string', starting_character: ['C'] },
          SHIPPRIORITY: { type: 'int', min: 0, max: 0 },
        },
        primary_key: 'O_ORDERKEY',
        foreign_keys: {
          O_CUSTKEY: ['C_CUSTKEY', 'customer'],
        },
      },
      part: {
        properties: {
          P_PARTKEY: { type: 'int', min: 1, max: 200 },
          P_NAME: {
            type: 'string',
            starting_character: ['b', 's', 'l', 'c', 'm', 'p', 'g', 't'],
          },
          MFGR: {
            type: 'enum',
            values: [
              'Manufacturer#1',
              'Manufacturer#2',
              'Manufacturer#3',
              'Manufacturer#4',
              'Manufacturer#5',
            ],
          },
          BRAND: {
            type: 'enum',
            values: [
              'Brand#13',
              'Brand#42',
              'Brand#34',
              'Brand#32',
              'Brand#24',
            ],
          },
          TYPE: {
            type: 'string',
            starting_character: ['S', 'M', 'E', 'P', 'L', 'STA', 'SMA'],
          },
          SIZE: { type: 'int', min: 1, max: 49 },
          CONTAINER: {
            type: 'string',
            starting_character: ['JUMBO', 'LG', 'WRAP', 'MED', 'SM'],
          },
          RETAILPRICE: { type: 'float', min: 901.0, max: 1100.2 },
        },
        primary_key: 'P_PARTKEY',
      },
      partsupp: {
        properties: {
          PS_PARTKEY: { type: 'int', min: 1, max: 50 },
          PS_SUPPKEY: { type: 'int', min: 2, max: 7551 },
          AVAILQTY: { type: 'int', min: 43, max: 9988 },
          SUPPLYCOST: { type: 'float', min: 14.78, max: 996.12 },
        },
        primary_key: ['PS_PARTKEY', 'PS_SUPPKEY'],
        foreign_keys: {
          PS_PARTKEY: ['P_PARTKEY', 'part'],
          PS_SUPPKEY: ['S_SUPPKEY', 'supplier'],
        },
      },
      region: {
        properties: {
          R_REGIONKEY: { type: 'int', min: 0, max: 4 },
          R_NAME: {
            type: 'string',
            starting_character: ['A', 'E', 'M', 'AFR', 'AME', 'ASI'],
          },
          R_COMMENT: {
            type: 'string',
            starting_character: ['l', 'h', 'g', 'u'],
          },
        },
        primary_key: 'R_REGIONKEY',
      },
      supplier: {
        properties: {
          S_SUPPKEY: { type: 'int', min: 1, max: 200 },
          S_NAME: { type: 'string', starting_character: ['S'] },
          S_ADDRESS: {
            type: 'string',
            starting_character: ['N', 'e', 'f', 'J', 'o', 'c', 'b', 'u'],
          },
          S_NATIONKEY: { type: 'int', min: 0, max: 24 },
          S_PHONE: {
            type: 'string',
            starting_character: [
              '1',
              '2',
              '3',
              '28-',
              '32-',
              '26-',
              '14-',
              '17-',
            ],
          },
          S_ACCTBAL: { type: 'float', min: -966.2, max: 9915.24 },
        },
        primary_key: 'S_SUPPKEY',
        foreign_keys: {
          S_NATIONKEY: ['N_NATIONKEY', 'nation'],
        },
      },
    },
  },
  customer: {
    entities: {
      customer: {
        primary_key: 'C_CUSTKEY',
        properties: {
          C_CUSTKEY: { type: 'int', min: 1, max: 1000 },
          C_NAME: { type: 'string', starting_character: ['A', 'B', 'C'] },
          C_STATUS: { type: 'enum', values: ['active', 'inactive'] },
        },
        foreign_keys: {},
      },
      order: {
        primary_key: 'O_ORDERKEY',
        properties: {
          O_ORDERKEY: { type: 'int', min: 1, max: 5000 },
          O_CUSTKEY: { type: 'int', min: 1, max: 1000 },
          O_TOTALPRICE: { type: 'float', min: 10.0, max: 1000.0 },
          O_ORDERSTATUS: {
            type: 'enum',
            values: ['pending', 'completed', 'cancelled'],
          },
        },
        foreign_keys: {
          O_CUSTKEY: ['C_CUSTKEY', 'customer'],
        },
      },
    },
  },
};
